import os
from utils.image_generator import ImageGenerator

deal_data = {
    'titulo': 'MOUSE WIRELESS SEM FIO E BLUETOOTH DELL MS3320W',
    'preco': 'R$ 131,05',
    'preco_original': 'R$ 176,00',
    'imagem': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png'
}

print("Gerando imagem de STORY (1080x1920)...")
story_path = ImageGenerator.generate(deal_data, mode="story")
if story_path:
    print(f"STORY gerado: {os.path.abspath(story_path)}")

print("\nGerando imagem de FEED (1080x1350)...")
feed_path = ImageGenerator.generate(deal_data, mode="feed")
if feed_path:
    print(f"FEED gerado: {os.path.abspath(feed_path)}")
