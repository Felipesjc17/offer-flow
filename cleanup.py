import os
import sys
import time

def main():
    print(">>> [Pre-Run] Verificando ambiente e limpando processos...")

    # 1. Limpeza de Processos do Chrome (Essencial para Selenium/Undetected-Chromedriver)
    # Isso evita erros de "SessionNotCreatedException" ou portas em uso.
    print(">>> [Pre-Run] Encerrando processos do Chrome e ChromeDriver...")
    
    if sys.platform == "win32":
        # Windows: /F (Força), /IM (Nome da Imagem), /T (Árvore de processos)
        # 2>nul oculta erros caso o processo não exista
        # os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
        os.system("taskkill /F /IM chromedriver.exe /T >nul 2>&1")
    else:
        # Linux/Mac
        # os.system("pkill -f chrome")
        os.system("pkill -f chromedriver")
    
    # Pausa para garantir que o Sistema Operacional liberou os recursos (arquivos/portas)
    time.sleep(2)
    print(">>> [Pre-Run] Processos limpos.")

    # 2. Verificação rápida do .env
    if not os.path.exists(".env"):
        print(">>> [AVISO] Arquivo .env não encontrado! A aplicação pode falhar.")

if __name__ == "__main__":
    main()