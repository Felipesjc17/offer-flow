import os
import sys
from dotenv import load_dotenv

load_dotenv()

from scrapers.mercado_livre import MercadoLivreScraper

print("=== TESTE DA API OFICIAL DO MERCADO LIVRE ===")
print("CLIENT_ID configurado:", os.getenv("MERCADO_LIVRE_CLIENT_ID"))
print("REDIRECT_URI configurada:", os.getenv("MERCADO_LIVRE_REDIRECT_URI"))

scraper = MercadoLivreScraper(limit=2)
try:
    deals = scraper.fetch_deals()
    print(f"\nBusca finalizada. Encontradas {len(deals)} ofertas.")
    for i, deal in enumerate(deals):
        print(f"\n--- Oferta {i+1} ---")
        print("Titulo:", deal["titulo"])
        print("Preco:", deal["preco"])
        print("Preco Original:", deal["preco_original"])
        print("Parcelamento:", deal["parcelamento"])
        print("Desconto:", deal["desconto_pix"])
        print("Imagem:", deal["imagem"])
        print("Link:", deal["link"])
except Exception as e:
    print("\n[Erro no teste]:", e)
