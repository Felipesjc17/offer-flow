import os
from utils.image_generator import ImageGenerator

deal_data = {
    'titulo': 'MOUSE WIRELESS SEM FIO E BLUETOOTH DELL MS3320W',
    'preco': 'R$ 131,05',
    'preco_original': 'R$ 176,00',
    # Using a reliable placeholder image URL for testing
    'imagem': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png'
}

print("Gerando imagem de teste (Story)...")
output_path = ImageGenerator.generate(deal_data, mode="story")
if output_path:
    print(f"Imagem gerada com sucesso em: {os.path.abspath(output_path)}")
else:
    print("Falha ao gerar a imagem.")
