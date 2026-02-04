# Visão Geral da API de Afiliados Shopee

## Funcionalidades Principais
*   Obter lista de ofertas.
*   Gerar link encurtado.
*   Obter relatório de conversão.

## Processo de Chamada da API
A plataforma utiliza a especificação **GraphQL** para lidar com as requisições. Por ser baseada em HTTP, integra-se facilmente com bibliotecas como cURL e Requests.

## Autenticação
Todas as requisições devem fornecer informações de autenticação através do cabeçalho `Authorization`.

### Estrutura do Cabeçalho
```text
Authorization: SHA256 Credential={AppId}, Timestamp={Timestamp}, Signature={Signature}
```

### Componentes
| Componente | Descrição |
| :--- | :--- |
| **SHA256** | Algoritmo utilizado (atualmente apenas SHA256). |
| **Credential** | O `AppId` obtido na plataforma de afiliados. |
| **Timestamp** | Timestamp Unix atual (segundos). A diferença para o servidor não pode exceder 10 minutos. |
| **Signature** | Assinatura de 256 bits (64 caracteres hexadecimais). |

### Cálculo da Assinatura (Signature)
Fórmula:
```text
Signature = SHA256(Credential + Timestamp + Payload + Secret)
```
*   **Payload:** O corpo da requisição em JSON (exatamente como será enviado).
*   **Secret:** Sua chave secreta de afiliado (não deve ser compartilhada).

## Limites de Uso (Rate Limit)
*   O sistema limita o número de chamadas de API em um período específico.
*   **Limite atual:** 2000 requisições por hora.
*   Se o limite for excedido, o sistema recusará o processamento até a próxima janela de tempo.

## Timestamp e Fuso Horário
A Shopee armazena dados usando o horário local (formato UTC+) de cada região, mas os timestamps representam um momento universal.

## Notas Importantes (Paginação e Scrollid)
Para consultar múltiplas páginas de dados, é necessário atenção ao mecanismo de `scrollid`:
1.  **Primeira Consulta:** Retorna o conteúdo da primeira página (máx. 500 itens) e um `scrollid`.
2.  **Páginas Seguintes:** É obrigatório usar o `scrollid` retornado para acessar a próxima página.
3.  **Validade:** O `scrollid` é válido por apenas **30 segundos** e é de uso único.
4.  **Intervalo:** Consultas iniciais (sem `scrollid`) exigem um intervalo de espera maior que 30 segundos entre elas.

## Relatórios de Conversão
*   **Período Disponível:** Últimos 3 meses.
*   O intervalo consultável na Open API é consistente com o portal do sistema de afiliados. Consultas fora desse intervalo retornarão erro.

## Ferramentas Úteis
Ferramenta oficial para testar requisições e verificar retornos:
Shopee Open API Explorer

## Requisição e Resposta

### Requisição
*   **Método:** `POST`
*   **Content-Type:** `application/json`
*   **Endpoint:** `https://open-api.affiliate.shopee.com.br/graphql`

**Formato do Corpo (JSON):**
```json
{
  "query": "...",
  "operationName": "...",
  "variables": { "myVariable": "someValue", ... }
}
```
*   `operationName` e `variables` são opcionais.
*   `operationName` é obrigatório apenas se houver múltiplas operações na query.

### Resposta
*   **Status HTTP:** 200 (se a requisição for recebida).
*   **Formato:** JSON.

**Estrutura:**
```json
{
  "data": { ... },
  "errors": [ ... ]
}
```

### Estrutura de Erro
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| message | String | Visão geral do erro. |
| path | String | Localização do erro na requisição. |
| extensions | Object | Detalhes do erro. |
| extensions.code | Int | Código do erro. |
| extensions.message | String | Descrição do erro. |

### Códigos de Erro
| Código | Significado | Descrição |
| :--- | :--- | :--- |
| 10000 | Erro de sistema | Erro interno do sistema. |
| 10010 | Erro de parsing | Sintaxe incorreta, tipo de campo incorreto, API inexistente, etc. |
| 10020 | Erro de autenticação | Assinatura incorreta ou expirada. |
| 10030 | Limite de tráfego | Número de requisições excede o limite. |
| 11000 | Erro de negócio | Erro no processamento de negócio. |

## Detalhes da API: Obter Lista de Ofertas (Get Shopee Offer List)

### Informações Gerais
*   **Query:** `shopeeOfferV2`
*   **Tipo de Retorno:** `ShopeeOfferConnectionV2!`

### Parâmetros da Query
| Campo | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| keyword | String | Busca por nome da oferta. | `clothes` |
| sortType | Int | Ordenação.<br>`1`: LATEST_DESC (Mais recente)<br>`2`: HIGHEST_COMMISSION_DESC (Maior comissão) | `1` |
| page | Int | Número da página. | `2` |
| limit | Int | Quantidade de dados por página. | `10` |

### Parâmetros de Resposta
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| nodes | [ShopeeOfferV2]! | Lista de dados das ofertas. |
| pageInfo | PageInfo! | Informações de paginação. |

### Estrutura do Objeto: ShopeeOfferV2
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| commissionRate | String | Taxa de comissão (ex: "0.0123" para 1.23%). |
| imageUrl | String | URL da imagem. |
| offerLink | String | Link da oferta. |
| originalLink | String | Link original. |
| offerName | String | Nome da oferta. |
| offerType | Int | `1`: Coleção (CAMPAIGN_TYPE_COLLECTION)<br>`2`: Categoria (CAMPAIGN_TYPE_CATEGORY) |
| categoryId | Int64 | Retornado quando offerType = 2. |
| collectionId | Int64 | Retornado quando offerType = 1. |
| periodStartTime | Int | Hora de início da oferta. |
| periodEndTime | Int | Hora de término da oferta. |

### Estrutura do Objeto: PageInfo
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| page | Int | Número da página atual. |
| limit | Int | Quantidade de dados por página. |
| hasNextPage | Bool | Se existe próxima página. |

## Detalhes da API: Obter Lista de Ofertas de Loja (Get Shop Offer List)

### Informações Gerais
*   **Query:** `shopOfferV2`
*   **Tipo de Retorno:** `ShopOfferConnectionV2`

### Parâmetros da Query
| Campo | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| shopId | Int64 | (Novo) Busca por ID da loja. | `84499012` |
| keyword | String | Busca por nome da loja. | `demo` |
| shopType | [Int] | (Novo) Filtra por tipo de loja.<br>`1`: OFFICIAL_SHOP<br>`2`: PREFERRED_SHOP<br>`4`: PREFERRED_PLUS_SHOP | `[],[1,4]` |
| isKeySeller | Bool | (Novo) Filtra ofertas de vendedores chave. | `true` |
| sortType | Int | Ordenação.<br>`1`: LATEST_DESC<br>`2`: HIGHEST_COMMISSION_DESC<br>`3`: POPULAR_SHOP_DESC | |
| sellerCommCoveRatio | String | (Novo) Razão de produtos com comissão. | `"", "0.123"` |
| page | Int | Número da página. | `2` |
| limit | Int | Quantidade de dados por página. | `10` |

### Parâmetros de Resposta
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| nodes | [ShopOfferV2]! | Lista de dados das ofertas. |
| pageInfo | PageInfo! | Informações de paginação. |

### Estrutura do Objeto: ShopOfferV2
| Campo | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| commissionRate | String | Taxa de comissão. | `"0.25"` |
| imageUrl | String | URL da imagem. | |
| offerLink | String | Link da oferta. | |
| originalLink | String | Link original. | |
| shopId | Int64 | ID da loja. | `84499012` |
| shopName | String | Nome da loja. | `Ikea` |
| ratingStar | String | (Novo) Avaliação da loja. | `"3.7"` |
| shopType | [Int] | (Novo) Tipo da loja. | |
| remainingBudget | Int | (Novo) Orçamento restante (0=Ilimitado, 3=Normal, 2=Baixo, 1=Muito Baixo). | `1` |
| periodStartTime | Int | Hora de início. | `1687712400` |
| periodEndTime | Int | Hora de término. | `1690822799` |
| sellerCommCoveRatio | String | (Novo) Razão de produtos com comissão. | |
| bannerInfo | BannerInfo | Informações do banner. | |

### Estrutura do Objeto: BannerInfo
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| count | Int | Quantidade de banners. |
| banners | [Banner!]! | Lista de banners. |

### Estrutura do Objeto: Banner
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| fileName | String | Nome do arquivo de imagem. |
| imageUrl | String | URL da imagem. |
| imageSize | Int | Tamanho da imagem. |
| imageWidth | Int | Largura da imagem. |
| imageHeight | Int | Altura da imagem. |

## Detalhes da API: Obter Lista de Ofertas de Produtos (Get Product Offer List)

### Informações Gerais
*   **Query:** `productOfferV2`
*   **Tipo de Retorno:** `ProductOfferConnectionV2`

### Parâmetros da Query
| Campo | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| shopId | Int64 | (Novo) Busca por ID da loja. | `84499012` |
| itemId | Int64 | (Novo) Busca por ID do item. | `17979995178` |
| productCatId | Int32 | (Novo) Filtra por categoria (Nível 1/2/3). | `100001` |
| listType | Int | Tipo de lista.<br>`0`: ALL<br>`2`: TOP_PERFORMING<br>`3`: LANDING_CATEGORY<br>`4`: DETAIL_CATEGORY<br>`5`: DETAIL_SHOP | `1` |
| matchId | Int64 | ID correspondente ao listType. | `10012` |
| keyword | String | Busca por nome do produto. | `shopee` |
| sortType | Int | Ordenação.<br>`1`: RELEVANCE_DESC<br>`2`: ITEM_SOLD_DESC<br>`3`: PRICE_DESC<br>`4`: PRICE_ASC<br>`5`: COMMISSION_DESC | `2` |
| page | Int | Número da página. | `2` |
| isAMSOffer | Bool | (Novo) Filtra ofertas com comissão AMS. | `true` |
| isKeySeller | Bool | (Novo) Filtra ofertas de vendedores chave. | `true` |
| limit | Int | Quantidade de dados por página. | `10` |

### Estrutura do Objeto: ProductOfferV2
| Campo | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| itemId | Int64 | ID do item. | `17979995178` |
| commissionRate | String | Taxa máxima de comissão. | `"0.25"` |
| sellerCommissionRate | String | (Novo) Taxa de comissão do vendedor. | `"0.25"` |
| shopeeCommissionRate | String | (Novo) Taxa de comissão da Shopee. | `"0.25"` |
| commission | String | (Novo) Valor da comissão. | `"27000"` |
| sales | Int32 | Quantidade vendida. | `25` |
| priceMax | String | (Novo) Preço máximo. | `"55.99"` |
| priceMin | String | (Novo) Preço mínimo. | `"45.99"` |
| productCatIds | [Int] | (Novo) IDs das categorias. | `[100012, ...]` |
| ratingStar | String | (Novo) Avaliação do produto. | `"4.7"` |
| priceDiscountRate | Int | (Novo) Taxa de desconto (%). | `10` |
| imageUrl | String | URL da imagem. | |
| productName | String | Nome do produto. | `IKEA starfish` |
| shopId | Int64 | (Novo) ID da loja. | `84499012` |
| shopName | String | Nome da loja. | `IKEA` |
| shopType | [Int] | (Novo) Tipo da loja. | `[], [1,4]` |
| productLink | String | Link do produto. | |
| offerLink | String | Link da oferta. | |
| periodStartTime | Int | Hora de início. | `1687539600` |
| periodEndTime | Int | Hora de término. | `1688144399` |

### Descrição de Códigos de Erro (Atualizado)
| Código | Descrição |
| :--- | :--- |
| 11000 | Erro de Negócio |
| 11001 | Erro de Parâmetros: {reason} |
| 11002 | Erro de Vinculação de Conta: {reason} |
| 10020 | Assinatura Inválida / App Desativado / Requisição Expirada / Timestamp Inválido / Credencial Inválida |
| 10030 | Limite de taxa excedido |
| 10031 | Acesso negado |
| 10032 | ID de afiliado inválido |
| 10033 | Conta congelada |
| 10034 | ID de afiliado na lista negra |
| 10035 | Sem acesso à plataforma Open API |

## Detalhes da API: Gerar Link Encurtado (Get Short Link)

### Informações Gerais
*   **Mutation:** `generateShortLink`
*   **Tipo de Retorno:** `ShortLinkResult!`

### Parâmetros da Mutation
| Campo | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| originUrl | String! | URL original. | `https://shopee.com.br/...` |
| subIds | [String] | Sub IDs para rastreamento (até 5). | `["s1","s2"]` |

### Estrutura do Objeto: ShortLinkResult
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| shortLink | String! | Link encurtado gerado. |

### Exemplo de Payload
```json
{"query":"mutation{\n    generateShortLink(input:{originUrl:\"https://shopee.com.br/...\",subIds:[\"s1\"]}){\n        shortLink\n    }\n}"}
```