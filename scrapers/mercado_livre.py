import os
import time
import sys
import random
import requests
import re
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from .base_scraper import BaseScraper
from database.database import deal_exists

class MercadoLivreScraper(BaseScraper):
    """
    Scraper para capturar ofertas do dia do Mercado Livre.
    Utiliza BeautifulSoup e rotaciona as paginas de ofertas para obter produtos variados.
    """
    def __init__(self, url=None, limit=5):
        if BeautifulSoup is None:
            print(">>> beautifulsoup4 nao instalado. Execute: pip install beautifulsoup4")
            sys.exit(1)
        self.limit = limit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }

    def _clean_installments(self, raw_text):
        """Limpa o texto do parcelamento para manter apenas a informacao util."""
        if not raw_text:
            return ""
        text = " ".join(raw_text.split())
        
        # Ignora informacoes que nao sejam parcelamento real
        if text.lower() == "outros meios" or "outros meios" in text.lower():
            return ""
            
        if " em " in text:
            text = text.split(" em ")[-1].strip()
        if text.lower().startswith("em "):
            text = text[3:].strip()
        return text

    def fetch_deals(self):
        """
        Coleta ofertas do dia do Mercado Livre.
        Rotaciona a pagina (1 a 15) para garantir ofertas frescas.
        """
        # Sorteia uma pagina entre 1 e 15
        page = random.randint(1, 15)
        url = f"https://www.mercadolivre.com.br/ofertas?page={page}"
        print(f">>> Acessando ofertas do Mercado Livre (Pagina {page}): {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"   [Erro ao acessar URL do Mercado Livre]: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all(class_='poly-card')
        
        if not cards:
            print("   [Aviso] Nenhum card 'poly-card' encontrado. A estrutura do site pode ter mudado.")
            return []

        produtos = []
        collected_count = 0
        
        for i, card in enumerate(cards):
            if collected_count >= self.limit:
                break
            try:
                # Titulo e Link
                link_elem = card.find('a', class_='poly-component__title')
                if not link_elem or not link_elem.get('href'):
                    continue
                link = link_elem['href']
                if "pdp_filters=" in link:
                    match = re.search(r'pdp_filters=([^&#]*)', link)
                    if match:
                        pdp_filters = match.group(0)
                        base_url = link.split("?")[0]
                        link = f"{base_url}?{pdp_filters}"
                    else:
                        link = link.split("?")[0]
                elif "?" in link:
                    link = link.split("?")[0]
                    
                if deal_exists(link):
                    continue

                titulo = link_elem.text.strip()

                # Preco Atual
                preco = ""
                preco_container = card.find('div', class_='poly-price__current')
                if preco_container:
                    preco_elem = preco_container.find(class_='andes-money-amount')
                    if preco_elem:
                        frac = preco_elem.find(class_='andes-money-amount__fraction')
                        cents = preco_elem.find(class_='andes-money-amount__cents')
                        preco = f"R$ {frac.text.strip()}" if frac else ""
                        if cents:
                            preco += f",{cents.text.strip()}"
                
                if not preco:
                    continue

                # Preco Original
                preco_original = ""
                preco_original_elem = card.find('s', class_='andes-money-amount--previous')
                if preco_original_elem:
                    frac_old = preco_original_elem.find(class_='andes-money-amount__fraction')
                    cents_old = preco_original_elem.find(class_='andes-money-amount__cents')
                    preco_original = f"R$ {frac_old.text.strip()}" if frac_old else ""
                    if cents_old:
                        preco_original += f",{cents_old.text.strip()}"

                # Parcelamento
                parcelamento = ""
                parcelamento_elem = card.find(class_='poly-price__installments')
                if parcelamento_elem:
                    parcelamento = self._clean_installments(parcelamento_elem.text)

                # Desconto (Pix / OFF)
                desconto_msg = ""
                desconto_elem = card.find(class_='andes-money-amount__discount')
                if desconto_elem:
                    desconto_msg = desconto_elem.text.strip()

                # Imagem
                img_elem = card.find('img', class_='poly-component__picture')
                imagem = None
                if img_elem:
                    imagem = img_elem.get('src') or img_elem.get('data-src')
                    if imagem:
                        # Substitui sufixos comuns de baixa resolucao por alta resolucao
                        imagem = re.sub(r'-[IVX]\.(jpg|png|gif|webp|jpeg)$', r'-O.\1', imagem, flags=re.IGNORECASE)
                        if imagem.startswith("http://"):
                            imagem = imagem.replace("http://", "https://", 1)

                # Cupom se houver no card
                cupom_desconto = None
                try:
                    coupon_elem = card.find(class_='poly-coupons__pill')
                    if coupon_elem:
                        txt = coupon_elem.text.strip()
                        if txt.lower().startswith("cupom "):
                            cupom_desconto = txt[6:].strip()
                        else:
                            cupom_desconto = txt
                        print(f"   [Cupom ML Encontrado] Desconto: {cupom_desconto}")
                except Exception:
                    pass

                produtos.append({
                    "titulo": titulo,
                    "preco": preco,
                    "preco_original": preco_original,
                    "parcelamento": parcelamento,
                    "desconto_pix": desconto_msg,
                    "link": link,
                    "imagem": imagem,
                    "cupom_codigo": None,
                    "cupom_desconto": cupom_desconto
                })
                print(f"   [Coletado ML] {titulo[:30]}...")
                collected_count += 1
            except Exception as e:
                print(f"   [Erro ao ler card {i} do Mercado Livre]: {e}")
                continue
        # Converte os links normais coletados em links de afiliados do Mercado Livre
        if produtos:
            try:
                produtos = self._convert_links_to_affiliate(produtos)
            except Exception as e:
                print(f">>> [Mercado Livre] Erro ao converter links para afiliados: {e}")
                
        return produtos

    def _convert_links_to_affiliate(self, deals):
        """
        Abre o navegador Chrome com a sessao persistida do usuario e
        converte os links originais em links de afiliados via JS Fetch.
        """
        if not deals:
            return deals
            
        try:
            import undetected_chromedriver as uc
        except ImportError:
            print(">>> [ML Affiliate] undetected_chromedriver nao instalado. Mantendo links originais.")
            return deals
            
        from .magazine_luiza import get_chrome_main_version
        
        session_path = os.path.join(os.getcwd(), "sessao_chrome")
        tag = os.getenv("MERCADO_LIVRE_AFFILIATE_TAG", "fs20251223173450")
        version = get_chrome_main_version() or 148
        
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={session_path}")
        options.add_argument("--disable-notifications")
        
        # Como o bot roda em segundo plano e ML possui forte deteccao headless (403),
        # nao usamos a flag --headless por padrao para garantir o sucesso da chamada.
        
        driver = None
        try:
            print(f"\n>>> [ML Affiliate] Iniciando navegador Chrome para gerar links de afiliados (Tag: {tag})...")
            driver = uc.Chrome(options=options, version_main=version)
            print(">>> [ML Affiliate] Acessando o Portal do Link Builder...")
            driver.get("https://www.mercadolivre.com.br/afiliados/linkbuilder")
            time.sleep(6) # Espera carregar a pagina
            
            # Verifica se esta autenticado ou deu erro
            if "Hubo un error" in driver.page_source or "login" in driver.current_url:
                print(">>> [ML Affiliate] AVISO: Usuario nao autenticado no linkbuilder do Mercado Livre.")
                print(">>> Por favor, execute 'python login_ml_affiliate.py' no terminal para realizar o login manual.")
                driver.quit()
                return deals
                
            js_script = """
            const callback = arguments[arguments.length - 1];
            const url = arguments[0];
            const affiliateTag = arguments[1];
            
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
            
            fetch('/affiliate-program/api/v2/affiliates/createLink', {
                method: 'POST',
                headers: {
                    'content-type': 'application/json',
                    'x-csrf-token': csrfToken
                },
                body: JSON.stringify({
                    urls: [url],
                    tag: affiliateTag
                })
            })
            .then(async res => {
                const text = await res.text();
                return {status: res.status, text: text};
            })
            .then(result => callback(result))
            .catch(err => callback({error: err.toString()}));
            """
            
            driver.set_script_timeout(15)
            
            for deal in deals:
                try:
                    orig_url = deal["link"]
                    print(f">>> [ML Affiliate] Gerando link de afiliado para: {deal['titulo'][:35]}...")
                    
                    result = driver.execute_async_script(js_script, orig_url, tag)
                    
                    if result.get("status") == 200:
                        import json
                        res_data = json.loads(result["text"])
                        if res_data.get("total_success", 0) > 0:
                            url_info = res_data["urls"][0]
                            short_link = url_info.get("short_url")
                            long_link = url_info.get("long_url")
                            
                            if short_link:
                                deal["link"] = short_link
                                print(f"   [Sucesso ML Affiliate] Link encurtado: {short_link}")
                            elif long_link:
                                deal["link"] = long_link
                                print(f"   [Sucesso ML Affiliate] Link longo: {long_link[:50]}...")
                        else:
                            error_msg = res_data["urls"][0].get("message", "Erro retornado pela API")
                            print(f"   [Erro ML Affiliate] Falha na API: {error_msg}")
                    else:
                        print(f"   [Erro ML Affiliate] HTTP {result.get('status')} ao tentar gerar link.")
                except Exception as ex:
                    print(f"   [Erro ML Affiliate] Falha ao processar link para '{deal['titulo'][:30]}': {ex}")
                    
            driver.quit()
        except Exception as e:
            print(f">>> [ML Affiliate] Erro geral ao gerar links de afiliados: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                    
        return deals

    def close(self):
        """Mantem a compatibilidade da interface."""
        pass
