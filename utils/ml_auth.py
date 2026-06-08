import os
import sys
import time
import json
import urllib.parse
import requests

TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml_tokens.json")

def get_ml_tokens():
    """
    Retorna os tokens de acesso do Mercado Livre.
    Faz o refresh automático se o token estiver expirado ou perto de expirar.
    """
    client_id = os.getenv("MERCADO_LIVRE_CLIENT_ID")
    client_secret = os.getenv("MERCADO_LIVRE_CLIENT_SECRET")
    redirect_uri = os.getenv("MERCADO_LIVRE_REDIRECT_URI")

    if not client_id or not client_secret or not redirect_uri:
        print(">>> [Mercado Livre Auth] Erro: Credenciais do Mercado Livre não configuradas no .env")
        return None

    tokens = {}
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                tokens = json.load(f)
        except Exception as e:
            print(f">>> [Mercado Livre Auth] Erro ao ler arquivo de tokens: {e}")

    # Verifica se os tokens já existem e não expiraram
    now = time.time()
    if tokens.get("access_token") and tokens.get("expires_at", 0) > (now + 300):
        return tokens

    # Se existe refresh token, faz a atualização (refresh)
    if tokens.get("refresh_token"):
        print(">>> [Mercado Livre Auth] Refresh token expirado. Renovando token de acesso...")
        url = "https://api.mercadolibre.com/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": tokens["refresh_token"]
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=15)
            response.raise_for_status()
            res_data = response.json()
            
            tokens["access_token"] = res_data["access_token"]
            tokens["refresh_token"] = res_data.get("refresh_token", tokens["refresh_token"])
            tokens["expires_at"] = time.time() + res_data["expires_in"]
            
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, indent=4)
            print(">>> [Mercado Livre Auth] Token renovado com sucesso.")
            return tokens
        except Exception as e:
            print(f">>> [Mercado Livre Auth] Falha ao renovar token com refresh_token: {e}")
            # Se falhou, tentará reautenticação

    # Se chegamos aqui, precisamos de um novo Authorization Code
    auth_code = os.getenv("MERCADO_LIVRE_AUTH_CODE")
    if not auth_code:
        # Gera a URL de autorização para o usuário
        encoded_uri = urllib.parse.quote(redirect_uri)
        auth_url = f"https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={client_id}&redirect_uri={encoded_uri}"
        
        print("\n" + "="*80)
        print("[MERCADO LIVRE AUTHENTICATION REQUIRED]")
        print("O robo precisa de autorizacao para acessar a API do Mercado Livre.")
        print(f"1. Acesse o seguinte link no seu navegador:\n\n   {auth_url}\n")
        print("2. Apos autorizar, voce sera redirecionado para a sua URL de retorno.")
        print("3. Copie o codigo gerado no parametro 'code' da barra de enderecos")
        print("   Exemplo: se a URL for https://site.com/home?code=TG-64b1f... copie apenas 'TG-64b1f...'")
        print("4. Cole este codigo no arquivo .env como MERCADO_LIVRE_AUTH_CODE=TG-xxxxxx e reinicie o robo,")
        print("   ou insira-o abaixo se estiver rodando no terminal interativo.")
        print("="*80 + "\n")
        
        # Verifica se estamos em terminal interativo
        if sys.stdin.isatty():
            try:
                auth_code = input("Insira o código 'code' (TG-...): ").strip()
            except KeyboardInterrupt:
                sys.exit(1)
        
        if not auth_code:
            raise Exception("Autenticação necessária do Mercado Livre. Configure a variável MERCADO_LIVRE_AUTH_CODE no arquivo .env")

    # Faz o login inicial com o Authorization Code
    print(f">>> [Mercado Livre Auth] Trocando código de autorização por tokens de acesso...")
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        res_data = response.json()
        
        tokens = {
            "access_token": res_data["access_token"],
            "refresh_token": res_data["refresh_token"],
            "expires_at": time.time() + res_data["expires_in"]
        }
        
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=4)
        print(">>> [Mercado Livre Auth] Autenticação realizada e tokens salvos com sucesso.")
        
        # Opcional: Se o código veio do .env, avise que ele já pode ser removido pois os tokens foram persistidos no ml_tokens.json
        if os.getenv("MERCADO_LIVRE_AUTH_CODE"):
            print(">>> [Mercado Livre Auth] NOTA: Você já pode remover a linha 'MERCADO_LIVRE_AUTH_CODE' do seu .env.")
            
        return tokens
    except Exception as e:
        err_msg = ""
        try:
            err_msg = response.text
        except:
            pass
        raise Exception(f"Falha ao obter token de acesso inicial do Mercado Livre: {e}. Detalhes: {err_msg}")
