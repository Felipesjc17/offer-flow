import os
import requests
from .base_poster import BasePoster
from utils.image_generator import ImageGenerator

class FacebookPoster(BasePoster):
    """
    Poster para publicar ofertas em uma Página do Facebook via Graph API.
    """
    def __init__(self, access_token, page_id):
        # Limpeza robusta do token
        token = access_token.strip().strip('"').strip("'")
        if token.lower().startswith("bearer"):
            token = token[6:].strip()

        self.access_token = token
        self.page_id = page_id.strip().strip('"').strip("'")
        # Base URL para fotos (mais visual para o Feed)
        self.photos_url = f"https://graph.facebook.com/v24.0/{self.page_id}/photos"
        self.feed_url = f"https://graph.facebook.com/v24.0/{self.page_id}/feed"

    def _get_page_token(self):
        """
        Tenta trocar o User Access Token (do .env) pelo Page Access Token.
        """
        try:
            url = f"https://graph.facebook.com/v24.0/{self.page_id}"
            params = {
                'fields': 'access_token',
                'access_token': self.access_token
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if resp.status_code == 200 and 'access_token' in data:
                return data['access_token']
        except Exception as e:
            print(f"   [Facebook] Aviso: Não foi possível obter token específico da página: {e}")
        return self.access_token

    def _post_story(self, deal_data, page_token):
        print(f">>> [Facebook] Preparando postagem no Story...")
        try:
            # Gera a imagem de Story
            local_path = ImageGenerator.generate(deal_data, mode="story")
            if not local_path:
                print("   [Facebook] Falha ao gerar imagem de Story.")
                return

            url = f"https://graph.facebook.com/v24.0/{self.page_id}/photo_stories"
            params = {'access_token': page_token}
            with open(local_path, 'rb') as img_file:
                files = {'source': ('story.jpg', img_file, 'image/jpeg')}
                resp = requests.post(url, params=params, files=files, timeout=60)
            resp.raise_for_status()
            print(f"   [Facebook] Story publicado! ID: {resp.json().get('id')}")
        except Exception as e:
            print(f"   [Facebook] Erro ao postar Story: {e}")

    def post_deal(self, deal_data):
        print(f">>> [Facebook] Preparando postagem no Feed: {deal_data['titulo'][:20]}...")
        final_token = self._get_page_token()

        # Gera a imagem de Feed (Menor, 1080x1350)
        local_path = ImageGenerator.generate(deal_data, mode="feed")

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

        msg_linhas.append("")
        msg_linhas.append("👇 Garanta o seu aqui:")
        msg_linhas.append(deal_data['link'])
        message = "\n".join(msg_linhas)

        try:
            if local_path:
                # Posta como FOTO (usando a imagem gerada)
                with open(local_path, 'rb') as img_file:
                    payload = {'message': message, 'access_token': final_token}
                    files = {'source': ('feed.jpg', img_file, 'image/jpeg')}
                    response = requests.post(self.photos_url, data=payload, files=files, timeout=45)
            else:
                # Fallback: Posta como LINK (comportamento antigo)
                payload = {'message': message, 'link': deal_data['link'], 'access_token': final_token}
                response = requests.post(self.feed_url, data=payload, timeout=30)

            response.raise_for_status()
            print(f"   [Facebook] Sucesso no Feed! ID: {response.json().get('id')}")

            # Posta no Story apenas se ativado
            if os.getenv("POST_STORY_FACEBOOK", "false").lower() == "true":
                self._post_story(deal_data, final_token)
            return True
        except Exception as e:
            print(f"   [Facebook] Erro ao postar: {e}")
            raise e