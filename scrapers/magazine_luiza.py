import os
import sys
import time
# Correção para Python 3.12+: O undetected_chromedriver precisa do distutils,
# que foi removido. Importar o setuptools restaura essa funcionalidade.
try:
    import setuptools
except ImportError:
    pass
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
uc_error = None
try:
    import undetected_chromedriver as uc
except Exception as e:
    uc = None
    uc_error = e

from .base_scraper import BaseScraper
from database.database import deal_exists

def get_chrome_main_version():
    """Tenta detectar a versão principal do Chrome instalado no Windows."""
    import subprocess
    import re
    
    commands = [
        r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
        r'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome" /v version',
        r'(Get-Item "C:\Program Files\Google\Chrome\Application\chrome.exe").VersionInfo.ProductVersion',
        r'(Get-Item "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe").VersionInfo.ProductVersion'
    ]
    
    for cmd in commands:
        try:
            if "reg query" in cmd:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                version = re.search(r'(\d+)\.', output)
                if version:
                    return int(version.group(1))
            else:
                # PowerShell commands
                ps_cmd = f"powershell -command \"{cmd}\""
                output = subprocess.check_output(ps_cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
                version = re.search(r'^(\d+)', output)
                if version:
                    return int(version.group(1))
        except:
            continue
    return None

class MagazineLuizaScraper(BaseScraper):
    def __init__(self, url, session_path, limit=3):
        if uc is None:
            print(f">>> ERRO DETALHADO AO IMPORTAR: {uc_error}")
            print(">>> undetected_chromedriver não instalado. Execute: pip install undetected-chromedriver")
            sys.exit(1)
        self.url = url
        self.session_path = session_path
        self.limit = limit
        self.driver = self._iniciar_driver()

    def _iniciar_driver(self):
        """Configura e inicia o WebDriver com persistência de sessão."""
        print(">>> Detectando versão do Chrome...")
        detected_version = get_chrome_main_version()
        if detected_version:
            print(f">>> Chrome v{detected_version} detectado.")
        else:
            detected_version = 148 # Fallback
            print(f">>> Versão não detectada, usando fallback v{detected_version}")

        print(">>> Iniciando Browser...")
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument(f"--user-data-dir={self.session_path}")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        
        driver = uc.Chrome(options=chrome_options, version_main=detected_version)
        return driver

    def fetch_deals(self):
        """Acessa a lista e coleta os dados básicos dos 3 primeiros produtos."""
        print(f">>> Acessando: {self.url}")
        self.driver.get(self.url)
        
        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="product-card-container"]')))
        time.sleep(2)

        cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="product-card-container"]')

        candidatos = []
        collected_count = 0
        for i, card in enumerate(cards):
            if collected_count >= self.limit:
                break
            try:
                link_original = card.get_attribute("href")
                if deal_exists(link_original):
                    continue

                titulo = card.find_element(By.CSS_SELECTOR, '[data-testid="product-title"]').text
                preco = card.find_element(By.CSS_SELECTOR, '[data-testid="price-value"]').text
                
                preco_original = ""
                try:
                    preco_original = card.find_element(By.CSS_SELECTOR, '[data-testid="price-original"]').text
                except:
                    pass

                parcelamento = ""
                try:
                    parcelamento = card.find_element(By.CSS_SELECTOR, '[data-testid="installment"]').text
                except:
                    pass

                desconto_pix = ""
                try:
                    desconto_elem = card.find_element(By.XPATH, ".//span[contains(., 'desconto no pix')]")
                    desconto_pix = desconto_elem.text
                except:
                    pass

                imagem = None
                try:
                    img_elem = card.find_element(By.CSS_SELECTOR, 'img[data-testid="image"]')
                    imagem = img_elem.get_attribute("src")
                except:
                    pass

                candidatos.append({
                    "titulo": titulo,
                    "preco": preco,
                    "preco_original": preco_original,
                    "parcelamento": parcelamento,
                    "desconto_pix": desconto_pix,
                    "link": link_original,
                    "imagem": imagem
                })
                print(f"   [Candidato] {titulo[:30]}...")
                collected_count += 1
            except Exception as e:
                print(f"   [Erro ao ler card {i}]: {e}")
                continue

        produtos = []
        for item in candidatos:
            try:
                print(f"   >>> Obtendo imagem HQ de: {item['titulo'][:30]}...")
                self.driver.get(item['link'])
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="image-selected-thumbnail"]')))
                img_hq = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="image-selected-thumbnail"]')
                if img_hq.get_attribute("src"):
                    item['imagem'] = img_hq.get_attribute("src")
            except Exception as e:
                print(f"   [Aviso] Falha ao obter imagem HQ: {e}")
            
            # Extrair cupom se existir
            item['cupom_codigo'] = None
            item['cupom_desconto'] = None
            try:
                coupon_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[data-testid="coupon-code-input"]')
                if coupon_inputs:
                    item['cupom_codigo'] = coupon_inputs[0].get_attribute("value")
                    try:
                        coupon_copy_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="coupon-code-copy"]')
                        strong_elem = coupon_copy_elem.find_element(By.TAG_NAME, 'strong')
                        item['cupom_desconto'] = strong_elem.text
                    except Exception as e_desc:
                        pass
                    print(f"   [Cupom Encontrado] Codigo: {item['cupom_codigo']}, Desconto: {item['cupom_desconto']}")
            except Exception as e_cupom:
                print(f"   [Aviso] Falha ao obter cupom: {e_cupom}")
            
            produtos.append(item)
            time.sleep(1)

        return produtos

    def close(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()
            print(">>> Navegador fechado.")
