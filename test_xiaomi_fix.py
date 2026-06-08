import os
from utils.image_generator import ImageGenerator

# Dados do produto que causou erro
deal_data = {
    'titulo': 'Smartphone Xiaomi Redmi Note 14 Lançamento 256GB 128GB Câmera 108MP 20MP até 12GB Ramboost AMOLED 120Hz FHD plus celular Design Premium - Unity',
    'preco': 'R$ 1.506,19',
    'preco_original': 'R$ 2.359,99',
    'parcelamento': '10x de R$ 177,20 sem juros',
    'desconto_pix': '15% de desconto no pix',
    'imagem': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png'
}

print("Gerando imagem de STORY (1080x1920) para o Xiaomi...")
story_path = ImageGenerator.generate(deal_data, mode="story")
if story_path:
    print(f"STORY gerado: {os.path.abspath(story_path)}")

print("\nGerando imagem de FEED (1080x1350) para o Xiaomi...")
feed_path = ImageGenerator.generate(deal_data, mode="feed")
if feed_path:
    print(f"FEED gerado: {os.path.abspath(feed_path)}")
