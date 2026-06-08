import requests
import time
import io
import os
import textwrap
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

from .base_poster import BasePoster
from utils.image_generator import ImageGenerator

class InstagramPoster(BasePoster):
    """
    Poster para publicar ofertas no Instagram Feed via Graph API.
    Requer uma conta Business (vinculada a uma página do Facebook OU usando Instagram Login).
    """
    def __init__(self, access_token, account_id):
        # Limpeza robusta do token
        token = access_token.strip().strip('"').strip("'")
        if token.lower().startswith("bearer"):
            token = token[6:].strip()
            
        self.access_token = token
        self.account_id = account_id.strip().strip('"').strip("'")
        self.base_url = f"https://graph.facebook.com/v24.0/{self.account_id}"
        self._id_checked = False

    def _check_and_fix_account_id(self):
        """
        Verifica se o ID configurado é de uma Página e tenta obter o ID do Instagram vinculado.
        """
        if self._id_checked:
            return

        try:
            url = f"https://graph.facebook.com/v24.0/{self.account_id}"
            params = {'fields': 'instagram_business_account,name', 'access_token': self.access_token}
            resp = requests.get(url, params=params, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if 'instagram_business_account' in data:
                    ig_id = data['instagram_business_account'].get('id')
                    if ig_id:
                        print(f"   [Instagram] 🔄 ID corrigido: Usando ID do Instagram: {ig_id}")
                        self.account_id = ig_id
                        self.base_url = f"https://graph.facebook.com/v24.0/{self.account_id}"
        except Exception as e:
            print(f"   [Instagram] Aviso: Falha ao verificar ID da conta: {e}")
        
        self._id_checked = True

    def _upload_to_imgur(self, file_path):
        client_id = os.getenv("IMGUR_CLIENT_ID")
        if not client_id: return None
        headers = {'Authorization': f'Client-ID {client_id}', 'User-Agent': 'Mozilla/5.0'}
        for attempt in range(3):
            try:
                with open(file_path, 'rb') as img:
                    resp = requests.post('https://api.imgur.com/3/image', headers=headers, files={'image': img}, timeout=30)
                resp.raise_for_status()
                return resp.json()['data']['link']
            except Exception:
                time.sleep(2)
        return None

    def _post_story(self, deal_data):
        print(f">>> [Instagram] Preparando postagem no Story...")
        local_path = ImageGenerator.generate(deal_data, mode="story")
        final_url = deal_data['imagem']
        if local_path:
            hosted = self._upload_to_imgur(local_path)
            if hosted: final_url = hosted
        try:
            create_url = f"{self.base_url}/media"
            payload = {'image_url': final_url, 'media_type': 'STORIES', 'access_token': self.access_token}
            resp = requests.post(create_url, data=payload, timeout=30)
            resp.raise_for_status()
            container_id = resp.json().get('id')
            ready = False
            for _ in range(6):
                time.sleep(5)
                r = requests.get(f"https://graph.facebook.com/v24.0/{container_id}", params={'fields': 'status_code', 'access_token': self.access_token}, timeout=10)
                if r.status_code == 200 and r.json().get('status_code') == 'FINISHED':
                    ready = True
                    break
            if ready:
                requests.post(f"{self.base_url}/media_publish", data={'creation_id': container_id, 'access_token': self.access_token}, timeout=30)
                print(f"   [Instagram] Story publicado!")
        except Exception as e:
            print(f"   [Instagram] Erro ao postar Story: {e}")

    def post_deal(self, deal_data):
        self._check_and_fix_account_id()
        print(f">>> [Instagram] Preparando postagem no Feed: {deal_data['titulo'][:20]}...")
        
        # Gera imagem customizada para o Feed
        local_path = ImageGenerator.generate(deal_data, mode="feed")
        final_url = deal_data['imagem']
        if local_path:
            hosted = self._upload_to_imgur(local_path)
            if hosted: final_url = hosted

        # Monta legenda detalhada (Estilo WhatsApp)
        msg_linhas = [f"🔥 {deal_data['titulo']} 🔥", ""]
        if deal_data.get('preco_original'):
            msg_linhas.append(f"De {deal_data['preco_original']}")
        if deal_data.get('parcelamento'):
            msg_linhas.append(f"Por apenas {deal_data['parcelamento']}")
        
        # Cupom de desconto se houver
        if deal_data.get('cupom_codigo') or deal_data.get('cupom_desconto'):
            if deal_data.get('cupom_codigo') and deal_data.get('cupom_desconto'):
                coupon_text = f"🎟️ *Cupom:* {deal_data['cupom_codigo']} ({deal_data['cupom_desconto']})"
            elif deal_data.get('cupom_codigo'):
                coupon_text = f"🎟️ *Cupom:* {deal_data['cupom_codigo']}"
            else:
                coupon_text = f"🎟️ *Cupom:* {deal_data['cupom_desconto']}"
            msg_linhas.append(coupon_text)

        # Pix
        if "magazine" in deal_data['link'].lower():
            msg_linhas.append(f"💰 {deal_data['preco']} no Pix")
        else:
            msg_linhas.append(f"💰 {deal_data['preco']}")
            
        if deal_data.get('desconto_pix'):
            # Usa o texto do desconto diretamente (evita parênteses duplos)
            msg_linhas.append(f"{deal_data['desconto_pix']}")
            
        msg_linhas.append("\n🔗 Link na Bio!")
        legenda = "\n".join(msg_linhas)

        payload = {
            'image_url': final_url, 
            'caption': legenda, 
            'access_token': self.access_token
        }
        try:
            resp = requests.post(f"{self.base_url}/media", data=payload, timeout=30)
            resp.raise_for_status()
            container_id = resp.json().get('id')
            ready = False
            for _ in range(6):
                time.sleep(5)
                r = requests.get(f"https://graph.facebook.com/v24.0/{container_id}", params={'fields': 'status_code', 'access_token': self.access_token}, timeout=10)
                if r.status_code == 200 and r.json().get('status_code') == 'FINISHED':
                    ready = True
                    break
            if ready:
                requests.post(f"{self.base_url}/media_publish", data={'creation_id': container_id, 'access_token': self.access_token}, timeout=30)
                print(f"   [Instagram] Feed publicado!")
            
            # Posta no Story apenas se ativado
            if os.getenv("POST_STORY_INSTAGRAM", "true").lower() == "true":
                self._post_story(deal_data)
            return True
        except Exception as e:
            print(f"   [Instagram] Erro ao postar Feed: {e}")
            raise e
