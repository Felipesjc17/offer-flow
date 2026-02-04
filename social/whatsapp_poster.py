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

        # Monta a mensagem com as novas informações
        msg_linhas = [f"🚨 *OFERTA DO DIA* 🚨\n", deal_data['titulo'], ""]
        
        if deal_data.get('preco_original'):
            msg_linhas.append(f"De ~{deal_data['preco_original']}~")
            
        if deal_data.get('parcelamento'):
            msg_linhas.append(f"Por apenas {deal_data['parcelamento']}")
            
        # Adiciona "no Pix" apenas se for Magazine Luiza (identificado pelo link)
        if "magazine" in deal_data['link'].lower():
            msg_linhas.append(f"{deal_data['preco']} no Pix")
        else:
            msg_linhas.append(f"{deal_data['preco']}")
        
        if deal_data.get('desconto_pix'):
            msg_linhas.append(f"{deal_data['desconto_pix']}")
            
        msg_linhas.append(f"\n👇 *Garanta o seu aqui:* \n{deal_data['link']}")
        
        mensagem = "\n".join(msg_linhas)

        # Tenta enviar com imagem
        if deal_data.get('imagem'):
            url_endpoint = f"{self.api_url}/message/sendMedia/{self.instance_name}"
            payload = {
                "number": self.chat_id,
                "media": deal_data['imagem'],
                "mediatype": "image",
                "caption": mensagem
            }
            print("   Enviando com imagem...")
        # Se não tiver imagem, envia só texto
        else:
            url_endpoint = f"{self.api_url}/message/sendText/{self.instance_name}"
            payload = {
                "number": self.chat_id,
                "text": mensagem
            }
            print("   Enviando apenas texto...")

        max_tentativas = 3
        for tentativa in range(1, max_tentativas + 1):
            try:
                response = requests.post(url_endpoint, json=payload, headers=self.headers)
                response.raise_for_status()  # Lança um erro para status HTTP 4xx/5xx
                print(f"   Oferta enviada com sucesso (Status: {response.status_code}).")
                return True
            except Exception as e:
                print(f"   !!! Erro ao enviar via API (Tentativa {tentativa}/{max_tentativas}): {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"   !!! Detalhes do erro: {e.response.text}")
                else:
                    print("   !!! Sem resposta do servidor.")
                if tentativa < max_tentativas:
                    time.sleep(5)
                else:
                    # Se falhar em todas as tentativas, lança o erro para ser capturado pelo app.py
                    raise e
        return False

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
