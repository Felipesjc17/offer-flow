import os
import time
import requests
from .base_poster import BasePoster

class WhatsappPoster(BasePoster):
    """
    Classe para postar ofertas no WhatsApp usando a Evolution API.
    """
    def __init__(self, api_url, api_key, instance_name, chat_id):
        self.api_url = api_url
        self.api_key = api_key
        self.instance_name = instance_name
        self.chat_id = chat_id
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def post_deal(self, deal_data):
        """
        Envia uma única oferta para o WhatsApp.
        """
        print(f">>> Enviando oferta via Evolution API: {deal_data['titulo'][:15]}...")

        # Monta a mensagem
        msg_linhas = [f"🚨 *OFERTA DO DIA* 🚨\n", deal_data['titulo'], ""]
        if deal_data.get('preco_original'):
            msg_linhas.append(f"De ~{deal_data['preco_original']}~")
        if deal_data.get('parcelamento'):
            msg_linhas.append(f"Por apenas {deal_data['parcelamento']}")
        
        # Cupom de desconto se houver
        if deal_data.get('cupom_codigo') or deal_data.get('cupom_desconto'):
            if deal_data.get('cupom_codigo') and deal_data.get('cupom_desconto'):
                coupon_text = f"🎟️ *Cupom:* `{deal_data['cupom_codigo']}` ({deal_data['cupom_desconto']})"
            elif deal_data.get('cupom_codigo'):
                coupon_text = f"🎟️ *Cupom:* `{deal_data['cupom_codigo']}`"
            else:
                coupon_text = f"🎟️ *Cupom:* {deal_data['cupom_desconto']}"
            msg_linhas.append(coupon_text)

        if "magazine" in deal_data['link'].lower():
            msg_linhas.append(f"{deal_data['preco']} no Pix")
        else:
            msg_linhas.append(f"{deal_data['preco']}")
        
        if deal_data.get('desconto_pix'):
            msg_linhas.append(f"{deal_data['desconto_pix']}")
            
        msg_linhas.append(f"\n👇 *Garanta o seu aqui:* \n{deal_data['link']}")
        mensagem = "\n".join(msg_linhas)

        url_endpoint = f"{self.api_url}/message/sendMedia/{self.instance_name}"
        
        # Preparação do Envio
        payload = {"number": self.chat_id, "mediatype": "image", "caption": mensagem}
        headers = {"apikey": self.api_key} # Importante: não forçar Content-Type para multipart

        is_local = deal_data.get('imagem') and os.path.exists(deal_data['imagem'])

        if is_local:
            print(f"   Enviando imagem local: {deal_data['imagem']}")
        elif deal_data.get('imagem'):
            print("   Enviando com URL de imagem...")
            payload["media"] = deal_data['imagem']
        else:
            print("   Enviando apenas texto...")
            url_endpoint = f"{self.api_url}/message/sendText/{self.instance_name}"
            payload = {"number": self.chat_id, "text": mensagem}

        max_tentativas = 3
        for tentativa in range(1, max_tentativas + 1):
            file_handle = None
            try:
                if is_local:
                    # Abre o arquivo a cada tentativa para garantir que o ponteiro esteja no início e o arquivo aberto
                    file_handle = open(deal_data['imagem'], 'rb')
                    files_payload = {'file': (os.path.basename(deal_data['imagem']), file_handle, 'image/jpeg')}
                    # Envio Multipart (Local)
                    response = requests.post(url_endpoint, data=payload, files=files_payload, headers=headers)
                else:
                    # Envio JSON (URL ou Texto)
                    response = requests.post(url_endpoint, json=payload, headers=self.headers)
                
                response.raise_for_status()
                print(f"   Oferta enviada com sucesso (Status: {response.status_code}).")
                
                if os.getenv("POST_STORY_WHATSAPP", "true").lower() == "true" and not deal_data.get('is_story_review'):
                    self._post_story(deal_data)
                
                return True
            except Exception as e:
                print(f"   !!! Erro ao enviar via API (Tentativa {tentativa}/{max_tentativas}): {e}")
                if tentativa < max_tentativas: time.sleep(5)
                else: raise e
            finally:
                if file_handle:
                    file_handle.close()
        return False

    def _post_story(self, deal_data):
        """
        Envia uma oferta para o Status/Story do WhatsApp.
        Nota: A Evolution API suporta envio para Status via endpoint de mensagem.
        """
        print(f">>> [WhatsApp] Preparando postagem no Status...")
        # Lógica para Status (opcional, dependendo da versão da Evolution API)
        # Por padrão, vamos focar no envio para o grupo/chat principal.
        pass

    def send_text(self, message):
        """
        Envia uma mensagem de texto simples para o chat configurado.
        Útil para logs de erro e notificações do sistema.
        """
        url_endpoint = f"{self.api_url}/message/sendText/{self.instance_name}"
        payload = {
            "number": self.chat_id,
            "text": message
        }
        
        try:
            response = requests.post(url_endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"   !!! Erro ao enviar notificação de texto: {e}")
            return False
