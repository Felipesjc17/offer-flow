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
├── .gitignore
├── deals.db               # (Gerado localmente) Banco de dados SQLite
├── MODULARIZATION_PRD.md
└── README.md
```

## Funcionalidade do Banco de Dados

Para evitar o envio repetido das mesmas ofertas, o sistema utiliza um banco de dados **SQLite** local.

- **Arquivo:** `deals.db` (criado automaticamente na raiz do projeto).
- **Função:** Armazena o link de cada oferta que já foi postada.
- **Git:** O arquivo `deals.db` é ignorado pelo `.gitignore` e não deve ser compartilhado entre diferentes ambientes.

## Configuração

1.  **Crie o arquivo de ambiente:**
    - Renomeie o arquivo `.env.example` para `.env`.
    - Preencha as variáveis. Deixar uma URL de scraper em branco desativará o scraper correspondente.

    ```dotenv
    # (Conteúdo do .env.example)
    ```

2.  **Instale as dependências:**
    ```bash
    pip install python-dotenv undetected-chromedriver requests beautifulsoup4
    ```

### Nota sobre Postagem no Instagram e Facebook

As implementações `InstagramPoster` e `FacebookPoster` são **placeholders (simulações)**. Elas não realizam postagens reais, apenas imprimem no console. A integração real requer desenvolvimento adicional com as APIs oficiais.

## Executando o Projeto

Para iniciar o processo, execute o script principal:

```bash
python app.py
```

O script irá:
1.  Inicializar o banco de dados `deals.db`.
2.  Executar cada scraper ativado para coletar ofertas.
3.  Verificar cada oferta no banco de dados. **Apenas ofertas novas (não registradas) serão processadas.**
4.  Para cada **oferta nova**, executar os posters ativados (WhatsApp, etc.).
5.  Registrar a oferta nova no banco de dados para evitar futuras duplicatas.

## Contribuição

Ao fazer alterações relevantes no projeto, lembre-se de **sempre atualizar este arquivo `README.md`**.
