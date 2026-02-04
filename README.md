# Sistema de Captura de Ofertas

Este projeto automatiza a captura de ofertas de sites de e-commerce e as publica em redes sociais, com um sistema de banco de dados para evitar postagens duplicadas.

## Estrutura do Projeto

O projeto é organizado de forma modular para facilitar a adição de novos scrapers e posters.

```
/
├── app.py                 # Ponto de entrada principal que orquestra os módulos
├── database/              # Módulo de gerenciamento do banco de dados
│   └── database.py
├── scrapers/              # Módulos de captura de ofertas
│   ├── base_scraper.py
│   ├── magazine_luiza.py
│   └── mercado_livre.py
├── social/                # Módulos de postagem em redes sociais
│   ├── base_poster.py
│   ├── whatsapp_poster.py
│   ├── instagram_poster.py  # (Simulação)
│   └── facebook_poster.py   # (Simulação)
├── .env                   # Arquivo para armazenar suas chaves de API
├── .env.example           # Arquivo de exemplo para o .env
├── requirements.txt       # Lista de dependências Python
├── .gitignore
├── deals.db               # (Gerado localmente) Banco de dados SQLite
├── MODULARIZATION_PRD.md
└── README.md
```

## Configuração do Ambiente

Siga estes passos para configurar e executar o projeto localmente.

### 1. Crie e Ative um Ambiente Virtual (Virtual Environment)

Para evitar conflitos de dependência, é altamente recomendado usar um ambiente virtual.

```bash
# Crie um ambiente virtual na pasta .venv
python -m venv .venv

# Ative o ambiente virtual
# No Windows (Git Bash ou MINGW64)
source .venv/Scripts/activate

# No Windows (Command Prompt)
# .venv\Scripts\activate.bat

# No macOS/Linux
# source .venv/bin/activate
```
**IMPORTANTE:** Todos os comandos a seguir devem ser executados com o ambiente virtual ativado.

### 2. Instale as Dependências Python

Com o ambiente virtual ativado, instale todas as dependências listadas no arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 3. Configure as Variáveis de Ambiente do Aplicativo

O arquivo `.env` armazena as URLs dos scrapers e as chaves de API.

- Renomeie o arquivo `.env.example` para `.env`.
- Preencha as variáveis. Deixar uma URL de scraper em branco desativará o scraper correspondente.
- **Atenção:** Certifique-se de definir a variável `AUTHENTICATION_API_KEY` no arquivo `.env`. Esta chave define a senha global da Evolution API (usada no login do Manager) e deve corresponder à variável `EVOLUTION_API_KEY` usada pelo script Python.
- **Limites de Produtos:** Você pode configurar a quantidade de produtos por site adicionando as variáveis:
    - `DEFAULT_PRODUCTS_LIMIT=2` (Padrão geral)
    - `MAGAZINE_LUIZA_LIMIT=5`
    - `MERCADO_LIVRE_LIMIT=5`
    - `SHOPEE_LIMIT=5`
- **Horário de Funcionamento:** Para limitar o horário de execução do robô:
    - `EXECUTION_START_HOUR=8` (Hora de início, ex: 8 para 08:00)
    - `EXECUTION_END_HOUR=22` (Hora de término, ex: 22 para 22:00)
- **Filtro de Preço:** Para evitar postar produtos muito baratos:
    - `MIN_PRICE_TO_POST=20.00` (Postar apenas produtos acima de R$ 20,00)
- **Filtros Shopee:**
    - `SHOPEE_MIN_SALES=20` (Mínimo de vendas para considerar a oferta)
    - `SHOPEE_MIN_RATING=4.0` (Avaliação mínima para considerar a oferta)
- **Ambientes e Monitoramento:**
    - `APP_ENV="production"` (Defina como `test` para usar o grupo de teste)
    - `WHATSAPP_CHAT_ID_TEST` (ID do grupo para testes, usado quando `APP_ENV=test`)
    - `WHATSAPP_ERROR_GROUP_ID` (ID do grupo para receber notificações de erros críticos e logs)

### 4. Configure e Inicie a API de WhatsApp (Evolution API)

Para que o envio de ofertas para o WhatsApp funcione, a **Evolution API** precisa estar rodando. O projeto usa Docker para simplificar esse processo.

**Pré-requisitos:**
*   [Docker](https://www.docker.com/products/docker-desktop/) instalado e em execução na sua máquina.

**Passos para iniciar a API:**

1.  **Configuração do Ambiente da API:**
    - O arquivo `docker-compose.yml` na raiz do projeto já contém as definições necessárias.
    - Ele utiliza o arquivo `.env` da raiz para carregar variáveis de ambiente adicionais, se necessário.

2.  **Inicie os Contêineres:**
    No diretório **raiz** do projeto, execute o comando a seguir para iniciar a API e seus serviços (banco de dados, etc.) em segundo plano.

    ```bash
    docker-compose up -d
    ```
    Este comando fará o download das imagens e iniciará os serviços. Pode levar alguns minutos na primeira vez.

3.  **Verifique o Status:**
    Para verificar se os serviços estão rodando, você pode usar o comando:
    ```bash
    docker-compose ps
    ```

4.  **Parando os Serviços:**
    Quando terminar de usar, pare os serviços com o comando:
    ```bash
    docker-compose down
    ```

## Executando o Projeto

### Opção 1: Execução Automática (Windows)

Para facilitar a execução no Windows, utilize o arquivo `run.bat`. Ele ativa o ambiente virtual, limpa processos antigos do Chrome (evitando erros de sessão) e inicia a aplicação.

Basta clicar duas vezes no arquivo `run.bat` na raiz do projeto ou executá-lo via terminal:

```cmd
run.bat
```

### Opção 2: Execução Manual

Com o ambiente virtual ativado e os serviços da Evolution API rodando, execute o script principal:

```bash
python app.py
```

O script irá:
1.  Inicializar o banco de dados `deals.db`.
2.  Executar cada scraper ativado para coletar ofertas.
3.  Verificar as ofertas no banco de dados para evitar duplicatas.
4.  Postar as **ofertas novas** usando os módulos ativados (WhatsApp, etc.).
5.  Registrar as novas ofertas no banco de dados.

## Solução de Problemas (Troubleshooting)

### Erro ao enviar para o Git (`git push`)

Se você receber um erro como `Updates were rejected because the remote contains work that you do not have locally`, significa que o repositório remoto no GitHub tem commits que você não tem na sua máquina local.

**Solução:** Baixe as alterações remotas e integre-as com as suas antes de enviar novamente.

```bash
# Baixa as alterações do repositório remoto e as mescla com sua branch local
git pull origin main

# Depois do pull, envie seus commits novamente
git push -u origin main
```

## Contribuição

Ao fazer alterações relevantes no projeto, lembre-se de **sempre atualizar este arquivo `README.md`**.