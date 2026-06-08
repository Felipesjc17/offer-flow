import os
import sys
import requests
from dotenv import load_dotenv, find_dotenv

# Adiciona o diretório pai ao path para importar módulos se necessário
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("--- Verificador de ID do Instagram ---")
    load_dotenv(find_dotenv())
    
    token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    
    if not token or not page_id:
        print("ERRO: Certifique-se de que FACEBOOK_ACCESS_TOKEN e FACEBOOK_PAGE_ID estão no .env")
        return

    print(f"Consultando Página ID: {page_id}...")
    
    url = f"https://graph.facebook.com/v24.0/{page_id}"
    params = {
        'fields': 'name,instagram_business_account',
        'access_token': token
    }
    
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        
        if 'error' in data:
            print(f"ERRO API: {data['error']['message']}")
            return
            
        print(f"Página encontrada: {data.get('name')}")
        
        if 'instagram_business_account' in data:
            ig_id = data['instagram_business_account'].get('id')
            print(f"\n✅ SUCESSO! ID do Instagram encontrado: {ig_id}")
            print(f"Atualize seu arquivo .env com:")
            print(f"INSTAGRAM_ACCOUNT_ID={ig_id}")
        else:
            print("\n❌ Nenhuma conta do Instagram vinculada a esta página foi encontrada.")
            print("Verifique se:")
            print("1. A conta do Instagram é Comercial/Criador.")
            print("2. A conta está vinculada à Página do Facebook nas configurações.")
            
    except Exception as e:
        print(f"Erro de conexão: {e}")

if __name__ == "__main__":
    main()
