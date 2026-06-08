import os
import sys
import time
import requests
from bs4 import BeautifulSoup

try:
    import setuptools
except ImportError:
    pass

try:
    import undetected_chromedriver as uc
except ImportError:
    print(">>> undetected_chromedriver não instalado. Execute: pip install undetected-chromedriver")
    sys.exit(1)

# Adiciona o diretório do projeto ao PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrapers.magazine_luiza import get_chrome_main_version

def main():
    print("=== ASSISTENTE DE LOGIN - MERCADO LIVRE AFILIADOS ===")
    
    session_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessao_chrome")
    print("Caminho do perfil Chrome:", session_path)
    
    print("Detectando versão do Chrome...")
    version = get_chrome_main_version()
    print(f"Versão detectada: {version}")
    
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={session_path}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    
    try:
        print("Iniciando navegador Chrome (com interface gráfica)...")
        driver = uc.Chrome(options=options, version_main=version)
        
        print("\nAcessando o Portal do Link Builder do Mercado Livre...")
        driver.get("https://www.mercadolivre.com.br/afiliados/linkbuilder")
        
        print("\n" + "="*80)
        print("INSTRUÇÕES:")
        print("1. Na janela do Chrome que acabou de abrir, faça o login na sua conta do Mercado Livre.")
        print("2. Certifique-se de acessar o Portal de Afiliados.")
        print("3. Quando o formulário do Link Builder (onde você cola links de produtos) estiver aparecendo na tela,")
        print("   volte para este terminal e pressione ENTER.")
        print("="*80 + "\n")
        
        input("Pressione [ENTER] quando estiver logado na página do Link Builder...")
        
        print("\nVerificando autenticação e cookies...")
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Procura pelo CSRF token
        csrf_meta = soup.find("meta", {"name": "csrf-token"})
        csrf_token = csrf_meta["content"] if csrf_meta else ""
        print(f"CSRF Token detectado: {csrf_token[:10]}... ({len(csrf_token)} caracteres)" if csrf_token else "Aviso: CSRF Token não encontrado na página.")
        
        # Coleta os cookies
        cookies = driver.get_cookies()
        print(f"Total de cookies capturados: {len(cookies)}")
        
        # Testa a requisição da API de criação de links
        print("\nTestando a API de afiliados de forma direta...")
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "content-type": "application/json",
            "origin": "https://www.mercadolivre.com.br",
            "referer": "https://www.mercadolivre.com.br/afiliados/linkbuilder",
            "x-csrf-token": csrf_token,
            "user-agent": driver.execute_script("return navigator.userAgent;")
        }
        
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
            
        test_url = "https://www.mercadolivre.com.br/nivel-a-laser-com-tripe-2-linhas-verde-autonivelante-20m/up/MLBU3901279854"
        payload = {
            "urls": [test_url],
            "tag": "achadostec"
        }
        
        api_url = "https://www.mercadolivre.com.br/affiliate-program/api/v2/affiliates/createLink"
        print(f"Enviando POST para {api_url}...")
        response = session.post(api_url, json=payload, headers=headers, timeout=15)
        
        print(f"Status Code da resposta: {response.status_code}")
        try:
            res_json = response.json()
            print("Resposta JSON da API:")
            import json
            print(json.dumps(res_json, indent=2, ensure_ascii=False))
        except Exception as e:
            print("Não foi possível decodificar a resposta como JSON:", e)
            print("Corpo da resposta:", response.text[:1000])
            
        print("\nConcluído! Você já pode fechar o navegador.")
        time.sleep(2)
        driver.quit()
        
    except Exception as e:
        print("\nErro ocorrido:", e)

if __name__ == "__main__":
    main()
