import time
import json
import hashlib
import requests
import os
import random
from .base_scraper import BaseScraper
from database.database import deal_exists

class ShopeeScraper(BaseScraper):
    def __init__(self, app_id=None, app_secret=None, limit=3):
        # Prioriza argumento, senão busca no ENV. Garante que ID seja string.
        self.app_id = str(app_id or os.getenv("SHOPEE_APP_ID") or "")
        self.app_secret = app_secret or os.getenv("SHOPEE_APP_SECRET") or ""

        try:
            self.min_sales = int(float(os.getenv("SHOPEE_MIN_SALES", 10)))
        except (ValueError, TypeError):
            self.min_sales = 19
        self.min_rating = float(os.getenv("SHOPEE_MIN_RATING", 4.0))

        if not self.app_id or not self.app_secret:
            print(">>> [Shopee] AVISO: Credenciais não encontradas. Verifique o .env")

        self.limit = limit
        # Endpoint GraphQL da Shopee Brasil
        self.url = "https://open-api.affiliate.shopee.com.br/graphql"

    def _generate_signature(self, payload_str, timestamp):
        """
        Gera a assinatura SHA256 conforme documentação:
        SHA256(Credential + Timestamp + Payload + Secret)
        """
        factor = f"{self.app_id}{timestamp}{payload_str}{self.app_secret}"
        signature = hashlib.sha256(factor.encode('utf-8')).hexdigest()
        return signature

    def fetch_deals(self):
        print(f">>> Acessando API Shopee: {self.url}")
        
        all_deals = []
        seen_links = set()
        
        # Lista de palavras-chave para garantir variedade de categorias
        keywords = [
            "smartphone", "smartwatch", "fone bluetooth", "notebook", 
            "tablet", "monitor gamer", "teclado", "mouse gamer", 
            "caixa de som", "alexa", "power bank", "câmera", 
            "tv 4k", "playstation", "xbox", "nintendo",
            "cadeira gamer", "drone", "projetor", "soundbar",
            "air fryer", "robô aspirador", "cafeteira", "microondas", "game", "pc", "ssd", "Hd", 
            "cartão de memória", "carregador", "cabo usb", "eletronico", "notebook", "impressora",
            "robo", "aspirador", "eletronico", "ventilador", "ferramenta", "furadeira", "parafusadeira",
            "smart tv", "geladeira", "fogão", "freezer", "lavadora", "secadora", "smartphone", "celular", "iphone", "xiaomi", "samsung", "motorola", "sony",
            "headphone", "headset", "earbuds", "tablet", "kindle", "e-reader", "smartwatch", "relógio inteligente", "massageador", "luminária", "smart home",
            "iluminação", "câmera de segurança", "roteador", "modem", "drone", "gopro", "fitness", "pulseira fitness",
            "carro", "soprador", "lavadora de alta pressão", "cortador de grama", "ferramenta elétrica", "serra elétrica", "brinquedo", 
            "caneca", "mochila", "relógio", "óculos de sol", "fones de ouvido", "cafeteira", "liquidificador", "batedeira", "air fryer", "panela elétrica", "processador de alimentos"
        ]
        random.shuffle(keywords)

        for kw in keywords:
            if len(all_deals) >= self.limit:
                break

            # Monta argumentos da query
            # Busca mais itens e varia a página para encontrar "próximos produtos" se os primeiros forem duplicados
            page = random.randint(1, 5)
            args_list = [f"page: {page}", f"limit: 20", f'keyword: "{kw}"']
            print(f"   [Shopee] Buscando por: {kw}")
            
            args_str = ", ".join(args_list)

            # Query GraphQL para buscar ofertas (ProductOfferV2 é comum para ofertas gerais)
            # Ajuste os campos conforme a necessidade real do seu projeto
            query = """
            {
                productOfferV2(%s) {
                    nodes {
                        productName
                        priceMin
                        imageUrl
                        offerLink
                        commissionRate
                        sales
                        ratingStar
                        priceDiscountRate
                    }
                }
            }
            """ % args_str

            # Prepara o payload. O json.dumps com separators remove espaços em branco
            # para garantir que o hash corresponda ao corpo enviado.
            payload_dict = {"query": query}
            payload_str = json.dumps(payload_dict, separators=(',', ':'))
            
            timestamp = int(time.time())
            signature = self._generate_signature(payload_str, timestamp)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={timestamp}, Signature={signature}"
            }

            try:
                response = requests.post(self.url, data=payload_str, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    print(f"   [Erro API Shopee] {data['errors']}")
                    continue

                if "data" in data and data["data"] and "productOfferV2" in data["data"]:
                    nodes = data["data"]["productOfferV2"]["nodes"]
                    if not nodes:
                        print(f"   [Shopee] Nenhum produto encontrado para {kw}.")

                    for node in nodes:
                        link = node.get("offerLink")
                        if not link:
                            continue

                        # Filtro de Vendas (Mínimo 20)
                        sales = node.get("sales") or 0
                        if int(sales) < self.min_sales:
                            print(f"   [Shopee] Ignorando (Vendas {sales} < {self.min_sales}): {node.get('productName')[:50]}...")
                            continue

                        # Filtro de Avaliação (Mínimo 4.0)
                        rating_str = node.get("ratingStar")
                        try:
                            rating = float(rating_str) if rating_str else 0.0
                        except (ValueError, TypeError):
                            rating = 0.0
                        
                        if rating < self.min_rating:
                            print(f"   [Shopee] Ignorando (Avaliação {rating} < {self.min_rating}): {node.get('productName')[:50]}...")
                            continue

                        # Verifica duplicatas na mesma execução e no banco de dados
                        if link in seen_links or deal_exists(link):
                            print(f"   [Shopee] Ignorando duplicata: {node.get('productName')[:50]}...")
                            continue
                        seen_links.add(link)

                        price = node.get("priceMin")
                        formatted_price = "Ver no site"
                        if price:
                            try:
                                # Garante que seja string e remove espaços antes de converter
                                price_val = float(str(price).strip())
                                formatted_price = f"R$ {price_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            except (ValueError, TypeError):
                                formatted_price = f"R$ {price}"

                        # Formata o desconto se houver
                        discount = node.get("priceDiscountRate")
                        discount_msg = None
                        if discount and int(discount) > 0:
                            discount_msg = f"🔥 {discount}% OFF"

                        all_deals.append({
                            "titulo": node.get("productName"),
                            "preco": formatted_price,
                            "link": link,
                            "imagem": node.get("imageUrl"),
                            "comissao": node.get("commissionRate"),
                            "desconto_pix": discount_msg
                        })
                        print(f"   [Shopee] Encontrado: {node.get('productName')[:50]}...")
                        # Encontrou um produto válido para esta categoria, passa para a próxima
                        break
                else:
                    print(f"   [Aviso Shopee] Resposta inesperada da API: {data}")
                
            except Exception as e:
                print(f"   [Erro Shopee] Falha na requisição para {kw}: {e}")
                continue
        
        return all_deals

    def close(self):
        """Método para manter compatibilidade com o app.py (não requer fechamento real)."""
        pass