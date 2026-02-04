import sys
import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from .base_scraper import BaseScraper
from database.database import deal_exists

class MercadoLivreScraper(BaseScraper):
    """
    Scraper para capturar ofertas do dia do Mercado Livre.
    Este scraper usa requests e BeautifulSoup, sendo mais leve que o Selenium.
    """
    def __init__(self, url, limit=5):
        if BeautifulSoup is None:
            print(">>> beautifulsoup4 não instalado. Execute: pip install beautifulsoup4")
            sys.exit(1)
        self.url = url
        self.limit = limit
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_deals(self):
        """
        Busca as ofertas na página de ofertas do dia do Mercado Livre.
        """
        print(f">>> Acessando: {self.url}")
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"   [Erro ao acessar URL do Mercado Livre]: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # A estrutura do Mercado Livre pode mudar, este seletor é um exemplo.
        # Ele busca pelos cards de promoção na seção de ofertas do dia.
        cards = soup.find_all('div', class_='promotion-item__container')

        produtos = []
        if not cards:
            print("   [Aviso] Nenhum card de produto encontrado com o seletor. A estrutura do site pode ter mudado.")

        collected_count = 0
        for i, card in enumerate(cards):
            if collected_count >= self.limit:
                break
            try:
                link_elem = card.find('a', class_='promotion-item__link-container')
                link = link_elem['href'] if link_elem else "Link não encontrado"
                if deal_exists(link):
                    continue

                titulo_elem = card.find('p', class_='promotion-item__title')
                titulo = titulo_elem.text.strip() if titulo_elem else "Título não encontrado"

                price_container = card.find('div', class_='andes-money-amount-combo__main-container')
                if price_container:
                    preco_elem = price_container.find('span', class_='andes-money-amount__fraction')
                    preco = f"R$ {preco_elem.text.strip()}" if preco_elem else "Preço não encontrado"
                else:
                    preco = "Preço não encontrado"

                preco_original_elem = card.find('s', class_='andes-money-amount-combo__previous-value')
                if preco_original_elem:
                    preco_original = preco_original_elem.find('span', class_='andes-money-amount__fraction').text
                    preco_original = f"R$ {preco_original.strip()}"
                else:
                    preco_original = ""
                
                img_elem = card.find('img', class_='promotion-item__img')
                imagem = img_elem['src'] if img_elem else None

                produtos.append({
                    "titulo": titulo,
                    "preco": preco,
                    "preco_original": preco_original,
                    "parcelamento": "", # O parcelamento principal não é facilmente visível no card
                    "desconto_pix": "", # Não é uma informação padrão no card
                    "link": link,
                    "imagem": imagem
                })
                print(f"   [Coletado] {titulo[:30]}...")
                collected_count += 1
            except Exception as e:
                print(f"   [Erro ao ler card {i} do Mercado Livre]: {e}")
                continue
        
        return produtos

    def close(self):
        """
        Método 'close' para manter a interface, embora não seja necessário para este scraper.
        """
        print(">>> Scraper do Mercado Livre finalizado (não requer fechamento de navegador).")
        pass
