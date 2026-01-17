import os
import time
from dotenv import load_dotenv, find_dotenv

# Importa todos os módulos necessários
from scrapers.magazine_luiza import MagazineLuizaScraper
from scrapers.mercado_livre import MercadoLivreScraper
from social.whatsapp_poster import WhatsappPoster
from social.instagram_poster import InstagramPoster
from social.facebook_poster import FacebookPoster
from database.database import init_db, deal_exists, add_deal

def main():
    """
    Orquestrador principal da aplicação.
    """
    load_dotenv(find_dotenv())
    
    # Inicializa o banco de dados
    init_db()

    # --- Configurações dos Scrapers ---
    scrapers = []
    if os.getenv("MAGAZINE_LUIZA_URL"):
        scrapers.append(MagazineLuizaScraper(
            url=os.getenv("MAGAZINE_LUIZA_URL"),
            session_path=os.path.join(os.getcwd(), "sessao_chrome")
        ))
    if os.getenv("MERCADO_LIVRE_URL"):
        scrapers.append(MercadoLivreScraper(url=os.getenv("MERCADO_LIVRE_URL")))

    # --- Coleta de Ofertas ---
    todas_as_ofertas = []
    if not scrapers:
        print(">>> ERRO: Nenhum scraper foi ativado. Verifique as URLs no arquivo .env.")
        return
        
    print(f">>> Iniciando automação com {len(scrapers)} scraper(s)...")
    for scraper in scrapers:
        try:
            print(f"\n--- Executando {scraper.__class__.__name__} ---")
            novas_ofertas = scraper.fetch_deals()
            if novas_ofertas:
                todas_as_ofertas.extend(novas_ofertas)
                print(f"   >>> {len(novas_ofertas)} ofertas encontradas por este scraper.")
            else:
                print("   >>> Nenhuma oferta encontrada por este scraper.")
        except Exception as e:
            print(f"   !!! Erro inesperado ao executar o scraper {scraper.__class__.__name__}: {e}")
        finally:
            scraper.close()

    # --- Filtragem de Ofertas Duplicadas ---
    if not todas_as_ofertas:
        print("\n>>> Nenhum produto foi coletado no total. Encerrando.")
    else:
        print(f"\n>>> {len(todas_as_ofertas)} ofertas coletadas no total. Verificando duplicatas no banco de dados...")
        ofertas_para_postar = []
        for oferta in todas_as_ofertas:
            if not deal_exists(oferta['link']):
                ofertas_para_postar.append(oferta)
            else:
                print(f"   [Ignorando] A oferta '{oferta['titulo'][:30]}...' já foi postada.")
        
        # --- Configuração dos Posters ---
        posters = []
        # (O código para popular a lista 'posters' permanece o mesmo)
        if os.getenv("POST_TO_WHATSAPP", "false").lower() == "true":
            if all([os.getenv("EVOLUTION_API_URL"), os.getenv("EVOLUTION_API_KEY"), os.getenv("EVOLUTION_INSTANCE_NAME"), os.getenv("WHATSAPP_CHAT_ID")]):
                posters.append(WhatsappPoster(
                    api_url=os.getenv("EVOLUTION_API_URL"),
                    api_key=os.getenv("EVOLUTION_API_KEY"),
                    instance_name=os.getenv("EVOLUTION_INSTANCE_NAME"),
                    chat_id=os.getenv("WHATSAPP_CHAT_ID")
                ))
            else:
                print("\n>>> AVISO: Postagem no WhatsApp ativada, mas as configurações da API estão incompletas no .env.")

        if os.getenv("POST_TO_INSTAGRAM", "false").lower() == "true":
            posters.append(InstagramPoster())
        
        if os.getenv("POST_TO_FACEBOOK", "false").lower() == "true":
            posters.append(FacebookPoster())

        # --- Envio das Ofertas Novas ---
        if not ofertas_para_postar:
            print("\n>>> Nenhuma oferta NOVA para postar.")
        elif not posters:
            print("\n>>> Nenhuma plataforma de postagem foi ativada. As ofertas não serão enviadas.")
        else:
            print(f"\n>>> {len(ofertas_para_postar)} novas ofertas para postar em {len(posters)} plataforma(s)...")
            for i, produto in enumerate(ofertas_para_postar):
                print(f"\n-- Postando Oferta {i+1}/{len(ofertas_para_postar)}: {produto['titulo'][:40]}... --")
                for poster in posters:
                    try:
                        poster.post_deal(produto)
                    except Exception as e:
                        print(f"   !!! Erro ao postar com {poster.__class__.__name__}: {e}")
                
                # Adiciona a oferta ao banco de dados para não ser postada novamente
                add_deal(produto['link'], produto['titulo'])
                print(f"   [Registrado] Oferta '{produto['titulo'][:30]}...' salva no banco de dados.")

                if i < len(ofertas_para_postar) - 1:
                    print("\n   ...aguardando para postar o próximo produto...")
                    time.sleep(10)

    print("\n>>> Automação finalizada.")

if __name__ == "__main__":
    main()
