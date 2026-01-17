
# Product Requirements Document: Modularização e Escalabilidade do Sistema de Captura de Ofertas

## 1. Introdução

Este documento descreve os requisitos para a modularização do sistema de captura de ofertas. O objetivo é refatorar o projeto atual para suportar a captura de promoções de múltiplos sites e a postagem em diversas redes sociais, garantindo ao mesmo tempo a segurança das chaves de API e a escalabilidade da arquitetura.

## 2. Visão Geral do Produto

O projeto tem como objetivo automatizar a busca por promoções em sites de e-commerce e compartilhá-las em redes sociais. A modularização permitirá que novas fontes de ofertas e novos canais de divulgação sejam adicionados com o mínimo de esforço e sem comprometer a segurança.

## 3. Requisitos Funcionais

### Fase 1: Refatoração do Núcleo e Segurança (Concluído)

Nesta fase, o foco é reorganizar o código existente, separar as configurações sensíveis e preparar a estrutura para futuras expansões.

- **R1.1: Gerenciamento de Configurações Sensíveis**
  - Todas as chaves de API, URLs, e outras informações sensíveis devem ser movidas para um arquivo `.env`.
  - O arquivo `app.py` e outros scripts devem ser atualizados para carregar essas variáveis a partir do `.env`.
  - O arquivo `.env` deve ser incluído no `.gitignore` para evitar que seja enviado ao repositório Git.

- **R1.2: Estrutura de Diretórios Modular**
  - O projeto deve ser organizado em uma estrutura de diretórios que separe as responsabilidades. A sugestão é:

    ```
    /
    ├── app.py                 # Ponto de entrada principal
    ├── scrapers/              # Módulos de captura de ofertas
    │   ├── __init__.py
    │   ├── base_scraper.py      # Classe base (abstrata) para scrapers
    │   └── magazine_luiza.py  # Implementação para Magazine Luiza
    ├── social/                # Módulos de postagem em redes sociais
    │   ├── __init__.py
    │   ├── base_poster.py       # Classe base para postagens
    │   └── (ex: twitter.py)     # Implementação futura
    ├── .env                   # Arquivo de configuração (ignorado pelo Git)
    ├── .gitignore
    └── README.md
    ```

### Fase 2: Arquitetura Escalável de Scrapers (Concluído)

O objetivo desta fase é criar um sistema onde novos scrapers possam ser adicionados de forma independente.

- **R2.1: Classe Base para Scrapers**
  - Criar uma classe abstrata `BaseScraper` em `scrapers/base_scraper.py`.
  - Esta classe deve definir uma interface comum para todos os scrapers, como um método `fetch_deals()`.

- **R2.2: Modularização do Scraper Existente**
  - O código de captura de ofertas do Magazine Luiza deve ser movido para a classe `MagazineLuizaScraper` no arquivo `scrapers/magazine_luiza.py`.
  - Esta classe deve herdar de `BaseScraper` e implementar o método `fetch_deals()`.

- **R2.3: Adição de um Novo Scraper (Exemplo)**
  - Para demonstrar a escalabilidade, um novo scraper para outro site (ex: "Loja Exemplo") deve ser criado em `scrapers/loja_exemplo.py`, seguindo a mesma estrutura.

### Fase 3: Arquitetura Escalável de Postagem em Redes Sociais (Concluído)

Similar à arquitetura de scrapers, esta fase prepara o sistema para postar em múltiplas redes sociais.

- **R3.1: Classe Base para Postagem**
  - Criar uma classe abstrata `BasePoster` em `social/base_poster.py`.
  - Esta classe deve definir uma interface comum para postagem, como um método `post_deal(deal_data)`.

- **R3.2: Implementação Inicial de Postagem**
  - Implementar classes para as redes sociais alvo, que herdam de `BasePoster` e implementam o método `post_deal`.

### Fase 4: Implementação de Persistência de Dados (Concluído)

Esta fase introduz um mecanismo de persistência para evitar o reenvio de ofertas já processadas.

- **R4.1: Banco de Dados para Evitar Duplicatas**
  - Implementar um banco de dados local (SQLite) para armazenar os links de todas as ofertas que foram postadas.
  - O sistema deve verificar neste banco de dados antes de postar uma nova oferta. Se a oferta já existir, ela deve ser ignorada.
  - O arquivo de banco de dados (`deals.db`) deve ser adicionado ao `.gitignore`.

## 4. Requisitos de Segurança

- **S1: Segredo de Chaves:** Nenhuma chave de API, senha ou outra informação sensível deve ser codificada diretamente no código-fonte. Todas devem ser gerenciadas através do arquivo `.env`.
- **S2: Controle de Versão:** O arquivo `.gitignore` deve ser configurado para ignorar arquivos de ambiente (`.env`), diretórios de dependências (`.venv/`, `node_modules/`), e outros arquivos que não devem ser versionados.

## 5. Cronograma Sugerido

- **Semana 1:** Conclusão da Fase 1.
- **Semana 2:** Conclusão da Fase 2.
- **Semana 3:** Conclusão da Fase 3.
- **Semana 4:** Conclusão da Fase 4.

## 6. Futuras Melhorias

- **Interface de Gerenciamento:** Criar uma interface web simples para adicionar/remover scrapers e gerenciar configurações.
- **Agendamento Robusto:** Utilizar um sistema de agendamento de tarefas mais robusto (ex: Celery, APScheduler) para executar os scrapers.
- **Logging e Monitoramento:** Implementar um sistema de logs para acompanhar a execução dos scrapers e identificar falhas.
