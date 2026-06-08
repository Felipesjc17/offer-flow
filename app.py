import os
import sys
import time
import random
from datetime import datetime, timedelta
import traceback
from dotenv import load_dotenv, find_dotenv

# Importa todos os módulos necessários
from scrapers.magazine_luiza import MagazineLuizaScraper
from scrapers.mercado_livre import MercadoLivreScraper
from scrapers.shopee import ShopeeScraper
from social.whatsapp_poster import WhatsappPoster
from social.instagram_poster import InstagramPoster
from social.facebook_poster import FacebookPoster
from database.database import init_db, deal_exists, add_deal, clean_old_deals
from utils.image_generator import ImageGenerator

class DualLogger:
    """Redireciona a saída (stdout/stderr) para o console e para um arquivo de log."""
    def __init__(self, filename="app.log"):
        self.terminal = sys.stdout
        self.filename = filename
        self.log = open(self.filename, "a", encoding="utf-8")
        self.last_check = time.time()
        self.new_line = True

    def _rotate_if_needed(self):
        # Verifica a cada 60 segundos para evitar chamadas excessivas ao sistema de arquivos
        if time.time() - self.last_check < 60:
            return
        self.last_check = time.time()

        try:
            if os.path.exists(self.filename):
                creation_time = os.path.getctime(self.filename)
                # 86400 segundos = 24 horas
                if (time.time() - creation_time) > 86400:
                    self.log.close()
                    
                    timestamp = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d_%H-%M-%S")
                    new_name = f"app_{timestamp}.log"
                    
                    if not os.path.exists(new_name):
                        os.rename(self.filename, new_name)
                    
                    self.log = open(self.filename, "a", encoding="utf-8")
                    self.write(f"\n>>> [Log Rotation] Log rotacionado. Antigo: {new_name}\n")
        except Exception as e:
            self.terminal.write(f"\n!!! Erro ao rotacionar log: {e}\n")

    def write(self, message):
        self._rotate_if_needed()
        
        if not message:
            return

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        lines = message.splitlines(keepends=True)

        for line in lines:
            if self.new_line and line != "\n":
                prefix = f"[{timestamp}] "
                self._safe_print(prefix)
                self.log.write(prefix)
            
            self._safe_print(line)
            self.log.write(line)
            self.new_line = line.endswith("\n")

        self.log.flush()

    def _safe_print(self, text):
        try:
            self.terminal.write(text)
        except Exception:
            # Fallback para terminais que não suportam UTF-8 (ex: Windows CP1252)
            try:
                encoding = getattr(self.terminal, 'encoding', 'utf-8') or 'utf-8'
                # Substitui caracteres problemáticos por '?'
                safe_text = text.encode(encoding, errors='replace').decode(encoding)
                self.terminal.write(safe_text)
            except Exception:
                pass

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def parse_price(price_str):
    """Converte string de preço (ex: 'R$ 1.200,50') para float."""
    if not price_str or not isinstance(price_str, str):
        return None
    try:
        # Remove R$ e espaços
        clean = price_str.replace("R$", "").strip()
        
        # Se for "Ver no site" ou vazio ou não começar com número
        if not clean or not clean[0].isdigit():
            return None

        # Remove pontos de milhar e troca vírgula por ponto decimal (Formato BR)
        clean = clean.replace(".", "").replace(",", ".")
        return float(clean)
    except (ValueError, IndexError):
        return None

def main():
    """
    Orquestrador principal da aplicação.
    """
    load_dotenv(find_dotenv())
    
    # Inicializa o banco de dados
    init_db()
    
    print(">>> Iniciando execução em loop (Intervalo: 20-35 min).")

    # Configuração do notificador de erros
    error_group_id = os.getenv("WHATSAPP_ERROR_GROUP_ID")
    error_poster = None
    if error_group_id and os.getenv("EVOLUTION_API_URL") and os.getenv("EVOLUTION_API_KEY") and os.getenv("EVOLUTION_INSTANCE_NAME"):
        error_poster = WhatsappPoster(
            api_url=os.getenv("EVOLUTION_API_URL"),
            api_key=os.getenv("EVOLUTION_API_KEY"),
            instance_name=os.getenv("EVOLUTION_INSTANCE_NAME"),
            chat_id=error_group_id
        )

    def notify_error(e, context=""):
        if error_poster:
            try:
                tb = traceback.format_exc()
                msg = f"🚨 *ERRO NO OFFER FLOW* 🚨\n\n*Contexto:* {context}\n*Erro:* {str(e)}\n\n*Traceback:*\n```{tb[:3000]}```"
                error_poster.send_text(msg)
            except Exception as ex:
                print(f"   !!! Falha ao enviar alerta para WhatsApp (Verifique se a API está rodando): {ex}")

    # Carrega URLs da Magazine Luiza do .env para a rotação
    magalu_urls = [url for url in [
        os.getenv("MAGAZINE_LUIZA_URL_SMARTPHONES"),
        os.getenv("MAGAZINE_LUIZA_URL_ELETRODOMESTICOS"),
        os.getenv("MAGAZINE_LUIZA_URL_VIDEO_TV"),
        os.getenv("MAGAZINE_LUIZA_URL_INFORMATICA")
    ] if url] # Apenas adiciona se a URL estiver definida no .env

    magalu_idx = 0

    while True:
        # --- Verificação de Horário de Funcionamento ---
        start_hour_env = os.getenv("EXECUTION_START_HOUR")
        end_hour_env = os.getenv("EXECUTION_END_HOUR")

        if start_hour_env is not None and end_hour_env is not None:
            try:
                start_hour = int(start_hour_env)
                end_hour = int(end_hour_env)
                
                now = datetime.now()
                current_hour = now.hour
                
                should_run = False
                if start_hour == end_hour:
                    should_run = True # Se iguais, roda sempre
                elif start_hour < end_hour:
                    should_run = start_hour <= current_hour < end_hour
                else: # Atravessa a meia-noite (ex: 22h as 06h)
                    should_run = current_hour >= start_hour or current_hour < end_hour
                
                if not should_run:
                    next_run = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    
                    wait_seconds = (next_run - now).total_seconds()
                    print(f"\n>>> Fora do horário de operação ({start_hour}h-{end_hour}h).")
                    print(f">>> Aguardando {wait_seconds/3600:.1f} horas (até {next_run.strftime('%d/%m/%Y %H:%M:%S')}) para iniciar.")
                    time.sleep(wait_seconds)
                    continue # Reinicia o loop para verificar novamente
            except ValueError as e:
                print(">>> ERRO: EXECUTION_START_HOUR ou EXECUTION_END_HOUR inválidos no .env. Ignorando restrição.")
                notify_error(e, "Configuração de Horário")

        print(f"\n>>> Iniciando novo ciclo em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        # Limpa ofertas antigas (mais de 48 horas) para permitir repostagem
        clean_old_deals(48)

        # Define a quantidade limite padrão de produtos (pode ser sobrescrito por scraper)
        default_limit = int(os.getenv("DEFAULT_PRODUCTS_LIMIT", 2))

        # Define o preço mínimo para postagem (0 = sem limite)
        min_price_env = os.getenv("MIN_PRICE_TO_POST")
        min_price = 0.0
        if min_price_env:
            try:
                min_price = float(str(min_price_env).replace(",", ".").strip())
            except ValueError:
                print(f">>> AVISO: MIN_PRICE_TO_POST inválido no .env ('{min_price_env}'). Desativando filtro de preço mínimo.")

        # --- Configurações dos Scrapers ---
        scrapers = []
        
        # Magazine Luiza com Rotação de URL
        current_magalu_url = magalu_urls[magalu_idx]
        
        # Extração de nome de categoria mais robusta
        try:
            parts = [p for p in current_magalu_url.split('/') if p]
            category_slug = parts[-1] if parts[-1] != 'l' else parts[-2]
            category_name = category_slug.replace('-', ' ').title()
        except Exception:
            category_name = "Ofertas"
            
        print(f">>> [Magalu] Ciclo atual focado em: {category_name}")
        
        limit = int(os.getenv("MAGAZINE_LUIZA_LIMIT", default_limit))
        scrapers.append(MagazineLuizaScraper(
            url=current_magalu_url,
            session_path=os.path.join(os.getcwd(), "sessao_chrome"),
            limit=limit
        ))
        
        # Rotaciona o índice para o próximo ciclo
        magalu_idx = (magalu_idx + 1) % len(magalu_urls)

        if os.getenv("MERCADO_LIVRE_URL"):
            limit = int(os.getenv("MERCADO_LIVRE_LIMIT", default_limit))
            scrapers.append(MercadoLivreScraper(url=os.getenv("MERCADO_LIVRE_URL"), limit=limit))
        if os.getenv("SHOPEE_APP_ID") and os.getenv("SHOPEE_APP_SECRET"):
            limit = int(os.getenv("SHOPEE_LIMIT", default_limit))
            scrapers.append(ShopeeScraper(limit=limit))

        # --- Coleta de Ofertas ---
        todas_as_ofertas = []
        if not scrapers:
            print(">>> ERRO: Nenhum scraper foi ativado. Verifique as URLs no arquivo .env.")
            # Aguarda um pouco antes de tentar novamente para não travar o loop em erro rápido
            time.sleep(60)
            continue
            
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
                notify_error(e, f"Execução do scraper {scraper.__class__.__name__}")
            finally:
                scraper.close()

        # --- Filtragem de Ofertas Duplicadas ---
        if not todas_as_ofertas:
            print("\n>>> Nenhum produto foi coletado no total.")
        else:
            print(f"\n>>> {len(todas_as_ofertas)} ofertas coletadas no total. Verificando duplicatas no banco de dados...")
            ofertas_para_postar = []
            for oferta in todas_as_ofertas:
                # Verifica duplicatas
                if deal_exists(oferta['link']):
                    print(f"   [Ignorando] A oferta '{oferta['titulo'][:30]}...' já foi postada.")
                    continue

                # Verifica preço mínimo (se configurado)
                if min_price > 0:
                    price_val = parse_price(oferta.get('preco'))
                    if price_val is not None and price_val < min_price:
                        print(f"   [Ignorando] Preço (R$ {price_val:.2f}) abaixo do mínimo (R$ {min_price:.2f}): {oferta['titulo'][:30]}...")
                        continue

                ofertas_para_postar.append(oferta)
            
            # --- Configuração dos Posters ---
            posters = []
            # (O código para popular a lista 'posters' permanece o mesmo)
            if os.getenv("POST_TO_WHATSAPP", "false").lower() == "true":
                # Lógica para alternar entre ambiente de Produção e Teste
                target_chat_id = os.getenv("WHATSAPP_CHAT_ID")
                app_env = os.getenv("APP_ENV", "production").lower()

                if app_env == "test":
                    test_chat_id = os.getenv("WHATSAPP_CHAT_ID_TEST")
                    if test_chat_id:
                        print(f">>> [Ambiente de Teste] Redirecionando mensagens para: {test_chat_id}")
                        target_chat_id = test_chat_id
                    else:
                        print(">>> [Aviso] Ambiente de teste configurado, mas WHATSAPP_CHAT_ID_TEST não definido. Usando produção.")

                if all([os.getenv("EVOLUTION_API_URL"), os.getenv("EVOLUTION_API_KEY"), os.getenv("EVOLUTION_INSTANCE_NAME"), target_chat_id]):
                    posters.append(WhatsappPoster(
                        api_url=os.getenv("EVOLUTION_API_URL"),
                        api_key=os.getenv("EVOLUTION_API_KEY"),
                        instance_name=os.getenv("EVOLUTION_INSTANCE_NAME"),
                        chat_id=target_chat_id
                    ))
                else:
                    print("\n>>> AVISO: Postagem no WhatsApp ativada, mas as configurações da API estão incompletas no .env.")

            if os.getenv("POST_TO_INSTAGRAM", "false").lower() == "true":
                ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
                ig_account = os.getenv("INSTAGRAM_ACCOUNT_ID")
                
                if ig_token and ig_account:
                    posters.append(InstagramPoster(
                        access_token=ig_token,
                        account_id=ig_account
                    ))
                else:
                    print("\n>>> AVISO: Postagem no Instagram ativada, mas credenciais (TOKEN/ACCOUNT_ID) incompletas no .env.")
            
            if os.getenv("POST_TO_FACEBOOK", "false").lower() == "true":
                fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
                fb_page = os.getenv("FACEBOOK_PAGE_ID")
                
                if fb_token and fb_page:
                    posters.append(FacebookPoster(
                        access_token=fb_token,
                        page_id=fb_page
                    ))
                else:
                    print("\n>>> AVISO: Postagem no Facebook ativada, mas credenciais (TOKEN/PAGE_ID) incompletas no .env.")

            # --- Review Mode (Sobrescreve posters se ativado) ---
            is_review_mode = os.getenv("REVIEW_MODE", "false").lower() == "true"
            review_group_id = os.getenv("WHATSAPP_REVIEW_GROUP_ID")
            
            if is_review_mode and review_group_id:
                print(f"\n>>> [REVIEW MODE] Ativado! Redirecionando TUDO para o grupo de revisão: {review_group_id}")
                # Substitui todos os posters por um único poster de WhatsApp voltado para o grupo de revisão
                posters = [WhatsappPoster(
                    api_url=os.getenv("EVOLUTION_API_URL"),
                    api_key=os.getenv("EVOLUTION_API_KEY"),
                    instance_name=os.getenv("EVOLUTION_INSTANCE_NAME"),
                    chat_id=review_group_id
                )]

            # --- Envio das Ofertas Novas ---
            if not ofertas_para_postar:
                print("\n>>> Nenhuma oferta NOVA para postar.")
            elif not posters:
                print("\n>>> Nenhuma plataforma de postagem foi ativada. As ofertas não serão enviadas.")
            else:
                # --- Mensagem de Cupons (Uma vez por ciclo antes das ofertas) ---
                coupon_url = os.getenv("MAGAZINE_LUIZA_COUPONS_URL", "https://especiais.magazineluiza.com.br/magazinevoce/cupons/?showcase=magazineachadostecbr")
                msg_cupons = (
                    "Vai comprar no Magazine Luiza?\n"
                    "🔥 Não perca nenhum desconto na sua compra.\n"
                    "🛒 Acesse o link abaixo e veja a lista de cupons disponíveis:\n"
                    f"{coupon_url}"
                )
                
                print(f"\n>>> Enviando mensagem de cupons para {len(posters)} plataforma(s)...")
                for poster in posters:
                    try:
                        # Envia principalmente no WhatsApp que aceita texto puro
                        if hasattr(poster, 'send_text'):
                            poster.send_text(msg_cupons)
                    except Exception as e:
                        print(f"   !!! Erro ao enviar mensagem de cupons com {poster.__class__.__name__}: {e}")

                print(f"\n>>> {len(ofertas_para_postar)} novas ofertas para postar em {len(posters)} plataforma(s)...")
                for i, produto in enumerate(ofertas_para_postar):
                    print(f"\n-- Postando Oferta {i+1}/{len(ofertas_para_postar)}: {produto['titulo'][:40]}... --")
                    
                    for poster in posters:
                        try:
                            poster.post_deal(produto)
                            
                            # Se estiver em modo de revisão, também gera e envia a imagem de STORY para o grupo
                            if is_review_mode and isinstance(poster, WhatsappPoster):
                                print("   [Review Mode] Aguardando para enviar imagem de Story...")
                                time.sleep(3) # Delay para evitar 429 da API
                                
                                print("   [Review Mode] Gerando imagem de Story para revisão...")
                                story_path = ImageGenerator.generate(produto, mode="story")
                                if story_path and os.path.exists(story_path):
                                    review_deal = produto.copy()
                                    # Agora o WhatsappPoster aceita caminho local
                                    review_deal['imagem'] = story_path
                                    review_deal['titulo'] = f"📸 {produto['titulo']}"
                                    review_deal['is_story_review'] = True
                                    
                                    story_review_group = os.getenv("WHATSAPP_STORY_REVIEW_GROUP_ID")
                                    if story_review_group:
                                        print(f"   [Review Mode] Enviando Story para o grupo específico: {story_review_group}")
                                        story_poster = WhatsappPoster(
                                            api_url=poster.api_url,
                                            api_key=poster.api_key,
                                            instance_name=poster.instance_name,
                                            chat_id=story_review_group
                                        )
                                        story_poster.post_deal(review_deal)
                                    else:
                                        poster.post_deal(review_deal)
                        except Exception as e:
                            print(f"   !!! Erro ao postar com {poster.__class__.__name__}: {e}")
                            traceback.print_exc()
                            notify_error(e, f"Postagem com {poster.__class__.__name__}")
                    
                    # Adiciona a oferta ao banco de dados para não ser postada novamente
                    add_deal(produto['link'], produto['titulo'])
                    print(f"   [Registrado] Oferta '{produto['titulo'][:30]}...' salva no banco de dados.")

                    if i < len(ofertas_para_postar) - 1:
                        print("\n   ...aguardando para postar o próximo produto...")
                        time.sleep(10)

        print("\n>>> Ciclo finalizado.")
        intervalo = random.randint(20, 40)
        proxima_execucao = datetime.now() + timedelta(minutes=intervalo)
        print(f">>> Aguardando {intervalo} minutos. Próxima execução às: {proxima_execucao.strftime('%d/%m/%Y %H:%M:%S')}")
        time.sleep(intervalo * 60)

if __name__ == "__main__":
    sys.stdout = DualLogger()
    sys.stderr = sys.stdout
    main()
