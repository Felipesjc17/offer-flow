import os
import requests
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Pega o token atual do .env (pode ser o de usuário que você gerou)
    token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    
    if not token or "SEU_TOKEN" in token:
        print("Erro: Configure o FACEBOOK_ACCESS_TOKEN no arquivo .env com o token que você gerou no Graph Explorer.")
        return

    print(f"Consultando API da Meta com o token: {token[:15]}...")
    
    # Consulta /me para ver permissões e /me/accounts para listar as páginas
    url = "https://graph.facebook.com/v24.0/me"
    params = {
        "fields": "id,name,permissions,accounts{access_token,name,id,instagram_business_account,tasks}",
        "access_token": token
    }
    
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        
        if "error" in data:
            print(f"\n❌ Erro na API: {data['error']['message']}")
            print("Dica: Gere um novo token no Graph Explorer com as permissões: pages_show_list, instagram_basic, pages_read_engagement")
            return

        print(f"\n✅ Token pertence a: {data.get('name')} (ID: {data.get('id')})")
        
        if "permissions" in data:
            perms = [p['permission'] for p in data['permissions']['data'] if p['status'] == 'granted']
            print(f"🔑 Permissões concedidas: {', '.join(perms)}")
            print("⚠️  Verifique se 'pages_manage_posts' e 'pages_read_engagement' estão na lista acima.")
            
            if 'pages_manage_posts' not in perms or 'pages_read_engagement' not in perms:
                print("\n❌ ERRO CRÍTICO: Faltam permissões obrigatórias!")
                print("   Gere um novo token no Graph Explorer e marque: pages_manage_posts, pages_read_engagement")
                return
        
        if "accounts" in data:
            print("\n>>> 🚀 PÁGINAS ENCONTRADAS (Copie estes dados para o seu .env):")
            for page in data["accounts"]["data"]:
                print("=" * 60)
                print(f"Página: {page['name']}")
                print(f"FACEBOOK_PAGE_ID={page['id']}")
                
                # Verifica tarefas (permissões) na página
                tasks = page.get('tasks', [])
                print(f"Permissões na página: {', '.join(tasks)}")
                
                # ESTE é o token que você deve usar no .env (Token da Página)
                print(f"FACEBOOK_ACCESS_TOKEN={page['access_token']}") 
                
                if "instagram_business_account" in page:
                    print(f"INSTAGRAM_ACCOUNT_ID={page['instagram_business_account']['id']}")
                else:
                    print("INSTAGRAM_ACCOUNT_ID=Não encontrado (Verifique se a conta do Instagram é Comercial e está vinculada à Página)")
                print("=" * 60)
        else:
            print("\nNenhuma página encontrada vinculada a este token. Verifique se o usuário é admin da página.")
            
    except Exception as e:
        print(f"Erro de conexão: {e}")

if __name__ == "__main__":
    main()