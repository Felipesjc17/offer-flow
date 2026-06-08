import os
import io
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
except ImportError:
    svg2rlg = None

class ImageGenerator:
    """
    Classe utilitária para gerar imagens de ofertas com a identidade visual Achados Tec BR.
    Suporta formatos de Story (1080x1920) e Feed (1080x1350).
    """
    
    @staticmethod
    def load_font(name, size):
        font_candidates = [name]
        if "ExtraBoldItalic" in name:
            font_candidates.extend(["impact.ttf", "seguibi.ttf", "arialbi.ttf"])
        elif "Black" in name:
            font_candidates.extend(["ariblk.ttf", "impact.ttf", "arialbd.ttf"])
        elif "Bold" in name or "ExtraBold" in name:
            font_candidates.extend(["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"])
        elif "Medium" in name:
            font_candidates.extend(["seguisb.ttf", "segoeui.ttf", "arial.ttf"])
        else:
            font_candidates.extend(["segoeui.ttf", "arial.ttf"])

        for font_file in font_candidates:
            try:
                return ImageFont.truetype(font_file, size)
            except IOError:
                try:
                    win_font = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', font_file)
                    return ImageFont.truetype(win_font, size)
                except IOError:
                    continue
        return ImageFont.load_default()

    @classmethod
    def generate(cls, deal_data, mode="story"):
        """
        Gera a imagem baseada no modo ('story' ou 'feed').
        """
        width = 1080
        height = 1920 if mode == "story" else 1350
        output_path = "story_achados_tec.jpg" if mode == "story" else "feed_achados_tec.jpg"

        # --- DESIGN TOKENS ---
        COLOR_BG = "#0078FF"
        COLOR_ACCENT = "#FFD700"
        COLOR_HIGHLIGHT = "#00E5FF"
        COLOR_TEXT_MAIN = "#FFFFFF"
        COLOR_CARD_BG = "#FFFFFF"
        COLOR_BUTTON_BG = "#34C759"
        COLOR_BUTTON_TEXT = "#FFFFFF"

        try:
            # 1. Obter imagem do produto
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(deal_data['imagem'], headers=headers, timeout=15)
            resp.raise_for_status()
            original_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")

            # 2. Canvas e Background
            template = Image.new("RGB", (width, height), COLOR_BG)
            draw = ImageDraw.Draw(template)

            # 3. Carregamento de Fontes
            font_header = cls.load_font("Montserrat-ExtraBoldItalic.ttf", 90 if mode == "story" else 75)
            font_title_heavy = cls.load_font("Montserrat-ExtraBold.ttf", 52 if mode == "story" else 48)
            font_price_label = cls.load_font("Montserrat-ExtraBold.ttf", 58 if mode == "story" else 50)
            font_price_value_old = cls.load_font("Montserrat-Bold.ttf", 75 if mode == "story" else 65)
            font_price_value_new = cls.load_font("Montserrat-ExtraBoldItalic.ttf", 130 if mode == "story" else 115)
            font_button = cls.load_font("Montserrat-ExtraBold.ttf", 55 if mode == "story" else 50)
            font_footer = cls.load_font("Montserrat-Bold.ttf", 42 if mode == "story" else 38)

            # 4. Cabeçalho
            header_text = "Oferta Imperdível!"
            bbox = draw.textbbox((0, 0), header_text, font=font_header)
            tw = bbox[2] - bbox[0]
            header_y = 140 if mode == "story" else 80
            draw.text(((width - tw) / 2 + 6, header_y + 6), header_text, font=font_header, fill="#000000")
            draw.text(((width - tw) / 2, header_y), header_text, font=font_header, fill=COLOR_ACCENT)

            # 5. Card do Produto
            card_w, card_h = 860, 700 if mode == "story" else 520
            card_x = (width - card_w) // 2
            card_y = 280 if mode == "story" else 180
            draw.rounded_rectangle((card_x + 15, card_y + 15, card_x + card_w + 15, card_y + card_h + 15), radius=60, fill="#000000")
            draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=60, fill=COLOR_CARD_BG)

            padding = 100
            img_w, img_h = original_img.size
            ratio = min((card_w - padding) / img_w, (card_h - padding) / img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))
            resized_img = original_img.resize(new_size, Image.LANCZOS)
            template.paste(resized_img, (card_x + (card_w - new_size[0]) // 2, card_y + (card_h - new_size[1]) // 2), resized_img if 'A' in resized_img.getbands() else None)

            # --- CUPOM BADGE ---
            if deal_data.get('cupom_codigo') or deal_data.get('cupom_desconto'):
                if deal_data.get('cupom_codigo') and deal_data.get('cupom_desconto'):
                    badge_txt = f"CUPOM: {deal_data['cupom_codigo']} ({deal_data['cupom_desconto']})"
                elif deal_data.get('cupom_codigo'):
                    badge_txt = f"CUPOM: {deal_data['cupom_codigo']}"
                else:
                    badge_txt = f"CUPOM: {deal_data['cupom_desconto']}"
                
                font_badge = cls.load_font("Montserrat-Black.ttf", 38 if mode == "story" else 34)
                
                # Medir texto
                bbox_b = draw.textbbox((0, 0), badge_txt, font=font_badge)
                bw = bbox_b[2] - bbox_b[0]
                bh = bbox_b[3] - bbox_b[1]
                
                badge_w = bw + 50
                badge_h = bh + 30
                
                # Posicionar no canto superior esquerdo do card
                bx = card_x + 30
                by = card_y + 30
                
                # Sombra
                draw.rounded_rectangle((bx + 5, by + 5, bx + badge_w + 5, by + badge_h + 5), radius=20, fill="#000000")
                # Fundo Vermelho Escuro / Carmesim
                draw.rounded_rectangle((bx, by, bx + badge_w, by + badge_h), radius=20, fill="#B71C1C")
                
                # Texto do Cupom
                draw.text((bx + 25, by + 12), badge_txt, font=font_badge, fill="#FFFFFF")

            # 6. Informações e Preço
            footer_y = height - (340 if mode == "story" else 260)
            available_space = footer_y - (card_y + card_h)
            
            # Título: Ajuste dinâmico de largura e linhas
            current_y = card_y + card_h + (available_space * (0.08 if mode == "story" else 0.05))
            titulo_formatado = deal_data['titulo']
            
            # Títulos muito longos usam fonte menor e mais linhas
            title_font_size = 52 if mode == "story" else 48
            wrap_width = 24 if mode == "story" else 28
            
            if len(titulo_formatado) > 80:
                title_font_size -= 8
                wrap_width += 6
                
            font_title_dyn = cls.load_font("Montserrat-ExtraBold.ttf", title_font_size)
            lines = textwrap.wrap(titulo_formatado, width=wrap_width)
            
            for line in lines[:3]: # Permite até 3 linhas para títulos gigantes
                bbox = draw.textbbox((0, 0), line, font=font_title_dyn)
                tw = bbox[2] - bbox[0]
                draw.text(((width - tw) / 2, current_y), line, font=font_title_dyn, fill=COLOR_TEXT_MAIN)
                current_y += (title_font_size + 12)

            # Container Preço
            price_card_w, price_card_h = 750, 260 if mode == "story" else 220
            price_card_x = (width - price_card_w) // 2
            price_card_y = current_y + (35 if mode == "story" else 20)
            draw.rounded_rectangle((price_card_x + 10, price_card_y + 10, price_card_x + price_card_w + 10, price_card_y + price_card_h + 10), radius=40, fill="#000000")
            draw.rounded_rectangle((price_card_x, price_card_y, price_card_x + price_card_w, price_card_y + price_card_h), radius=40, fill="#FFFFFF")

            # Conteúdo Preço
            label_por, val_por = "POR: ", deal_data['preco']
            has_old = 'preco_original' in deal_data and deal_data['preco_original']
            has_installments = 'parcelamento' in deal_data and deal_data['parcelamento']
            
            # Define fontes base
            current_font_price = font_price_value_new
            font_installments = cls.load_font("Montserrat-Bold.ttf", 55 if mode == "story" else 48)
            
            # --- Ajuste Dinâmico de Layout ---
            if has_installments:
                # Prepara os textos
                txt_inst = f"Por apenas {deal_data['parcelamento']}"
                txt_pix = f"ou {deal_data['preco']} no Pix"
                
                # 1. Ajuste Dinâmico da Fonte do Parcelamento (Aumentada conforme pedido)
                inst_font_size = 62 if mode == "story" else 52
                current_font_inst = cls.load_font("Montserrat-Bold.ttf", inst_font_size)
                bbox_inst = draw.textbbox((0, 0), txt_inst, font=current_font_inst)
                while (bbox_inst[2]-bbox_inst[0]) > (price_card_w - 60) and inst_font_size > 40:
                    inst_font_size -= 2
                    current_font_inst = cls.load_font("Montserrat-Bold.ttf", inst_font_size)
                    bbox_inst = draw.textbbox((0, 0), txt_inst, font=current_font_inst)

                # 2. Ajuste Dinâmico da Fonte do Pix
                pix_font_size = 100 if mode == "story" else 90
                current_font_pix = cls.load_font("Montserrat-ExtraBoldItalic.ttf", pix_font_size)
                bbox_pix = draw.textbbox((0, 0), txt_pix, font=current_font_pix)
                while (bbox_pix[2]-bbox_pix[0]) > (price_card_w - 60) and pix_font_size > 50:
                    pix_font_size -= 4
                    current_font_pix = cls.load_font("Montserrat-ExtraBoldItalic.ttf", pix_font_size)
                    bbox_pix = draw.textbbox((0, 0), txt_pix, font=current_font_pix)

                h_inst = bbox_inst[3] - bbox_inst[1]
                h_pix = bbox_pix[3] - bbox_pix[1]
                
                # 3. Ajuste do Preço Original (De:) - Menor e posicionado acima
                h_old = 0
                if has_old:
                    val_de = deal_data['preco_original']
                    old_font_size = 60 if mode == "story" else 55 # Reduzida
                    current_font_old = cls.load_font("Montserrat-Bold.ttf", old_font_size)
                    bbox_v_old = draw.textbbox((0, 0), val_de, font=current_font_old)
                    max_old_w = price_card_w - 150 
                    while (bbox_v_old[2]-bbox_v_old[0]) > max_old_w and old_font_size > 35:
                        old_font_size -= 4
                        current_font_old = cls.load_font("Montserrat-Bold.ttf", old_font_size)
                        bbox_v_old = draw.textbbox((0, 0), val_de, font=current_font_old)
                    h_old = bbox_v_old[3] - bbox_v_old[1]

                # Cálculo de altura total para centralização vertical (dentro do container)
                spacing = 10
                total_content_h = h_inst + spacing + h_pix
                if has_old:
                    total_content_h += h_old + spacing
                    
                # Centraliza mas sobe um pouco mais (subtrai 15px do y inicial)
                inner_y = price_card_y + (price_card_h - total_content_h) // 2 - 15
                if inner_y < price_card_y + 10: inner_y = price_card_y + 10
                
                # Desenha o "DE:" (Dentro do container agora)
                if has_old:
                    label_de = "DE: "
                    font_de_label_small = cls.load_font("Montserrat-ExtraBold.ttf", 45 if mode == "story" else 40)
                    bbox_l = draw.textbbox((0, 0), label_de, font=font_de_label_small)
                    tw_total = (bbox_l[2]-bbox_l[0]) + (bbox_v_old[2]-bbox_v_old[0]) + 10
                    tx = price_card_x + (price_card_w - tw_total) // 2
                    
                    draw.text((tx, inner_y + (h_old // 4)), label_de, font=font_de_label_small, fill="#0078FF")
                    tx_v = tx + (bbox_l[2]-bbox_l[0]) + 10
                    draw.text((tx_v, inner_y), val_de, font=current_font_old, fill="#666666")
                    line_y = inner_y + (h_old // 2) + 5
                    draw.line((tx_v - 5, line_y, tx_v + (bbox_v_old[2]-bbox_v_old[0]) + 5, line_y), fill="#FF0000", width=5)
                    inner_y += h_old + spacing

                # Desenha Linha 1: Parcelamento
                tx_inst = price_card_x + (price_card_w - (bbox_inst[2]-bbox_inst[0])) // 2
                draw.text((tx_inst, inner_y), txt_inst, font=current_font_inst, fill="#000000")
                
                # Desenha Linha 2: Pix
                inner_y += h_inst + spacing
                tx_pix = price_card_x + (price_card_w - (bbox_pix[2]-bbox_pix[0])) // 2
                draw.text((tx_pix, inner_y), txt_pix, font=current_font_pix, fill="#000000")
                
            else:
                # Caso simplificado (apenas um preço)
                val_por = deal_data['preco']
                current_font_price = font_price_value_new
                max_val_w = price_card_w - 200 
                bbox_v_p = draw.textbbox((0, 0), val_por, font=current_font_price)
                val_w = bbox_v_p[2] - bbox_v_p[0]
                price_font_size = 130 if mode == "story" else 115
                while val_w > max_val_w and price_font_size > 60:
                    price_font_size -= 5
                    current_font_price = cls.load_font("Montserrat-ExtraBoldItalic.ttf", price_font_size)
                    bbox_v_p = draw.textbbox((0, 0), val_por, font=current_font_price)
                    val_w = bbox_v_p[2] - bbox_v_p[0]

                h_new = bbox_v_p[3] - bbox_v_p[1]
                
                h_old = 0
                if has_old:
                    val_de = deal_data['preco_original']
                    old_font_size = 60 if mode == "story" else 55
                    current_font_old = cls.load_font("Montserrat-Bold.ttf", old_font_size)
                    bbox_v_old = draw.textbbox((0, 0), val_de, font=current_font_old)
                    while (bbox_v_old[2]-bbox_v_old[0]) > (price_card_w - 150) and old_font_size > 35:
                        old_font_size -= 4
                        current_font_old = cls.load_font("Montserrat-Bold.ttf", old_font_size)
                        bbox_v_old = draw.textbbox((0, 0), val_de, font=current_font_old)
                    h_old = bbox_v_old[3] - bbox_v_old[1]

                spacing = 15
                total_content_h = (h_old + spacing + h_new) if has_old else h_new
                inner_y = price_card_y + (price_card_h - total_content_h) // 2 - 10

                if has_old:
                    label_de = "DE: "
                    font_de_label_small = cls.load_font("Montserrat-ExtraBold.ttf", 45 if mode == "story" else 40)
                    bbox_l = draw.textbbox((0, 0), label_de, font=font_de_label_small)
                    tw_total = (bbox_l[2]-bbox_l[0]) + (bbox_v_old[2]-bbox_v_old[0]) + 10
                    tx = price_card_x + (price_card_w - tw_total) // 2
                    draw.text((tx, inner_y + (h_old // 4)), label_de, font=font_de_label_small, fill="#0078FF")
                    tx_v = tx + (bbox_l[2]-bbox_l[0]) + 10
                    draw.text((tx_v, inner_y), val_de, font=current_font_old, fill="#666666")
                    line_y = inner_y + (h_old // 2) + 5
                    draw.line((tx_v - 5, line_y, tx_v + (bbox_v_old[2]-bbox_v_old[0]) + 5, line_y), fill="#FF0000", width=5)
                    inner_y += h_old + spacing

                label_por = "POR: "
                bbox_l_p = draw.textbbox((0, 0), label_por, font=font_price_label)
                tw_total_p = (bbox_l_p[2]-bbox_l_p[0]) + val_w + 15
                tx_p = price_card_x + (price_card_w - tw_total_p) // 2
                label_y = inner_y + (h_new - (bbox_l_p[3]-bbox_l_p[1])) // 2
                draw.text((tx_p, label_y), label_por, font=font_price_label, fill="#0078FF")
                draw.text((tx_p + (bbox_l_p[2]-bbox_l_p[0]) + 15, inner_y), val_por, font=current_font_price, fill="#000000")

            # 7. Botão (Apenas no Story)
            if mode == "story":
                btn_txt = "ENTRE NO GRUPO VIP"
                btn_w, btn_h = 820, 140
                btn_x = (width - btn_w) // 2
                draw.rounded_rectangle((btn_x + 8, footer_y + 8, btn_x + btn_w + 8, footer_y + btn_h + 8), radius=70, fill="#000000")
                draw.rounded_rectangle((btn_x, footer_y, btn_x + btn_w, footer_y + btn_h), radius=70, fill=COLOR_BUTTON_BG)

                bbox_btn = draw.textbbox((0, 0), btn_txt, font=font_button)
                bw, bh = bbox_btn[2] - bbox_btn[0], bbox_btn[3] - bbox_btn[1]
                icon_size = 70
                icon_gap = 25
                content_w = bw + icon_gap + icon_size
                tx = btn_x + (btn_w - content_w) // 2
                draw.text((tx, footer_y + (btn_h - bh) // 2 - 22), btn_txt, font=font_button, fill=COLOR_BUTTON_TEXT)

                # Ícone WhatsApp
                ix, iy_p = tx + bw + icon_gap, footer_y + (btn_h - icon_size) // 2 - 2
                svg_path = os.path.join(os.getcwd(), "assets", "icons", "WhatsApp.svg")
                if svg2rlg and os.path.exists(svg_path):
                    try:
                        drawing = svg2rlg(svg_path)
                        scaling_factor = icon_size / drawing.width
                        drawing.width *= scaling_factor
                        drawing.height *= scaling_factor
                        drawing.scale(scaling_factor, scaling_factor)
                        png_buffer = io.BytesIO()
                        renderPM.drawToFile(drawing, png_buffer, fmt="PNG", bg=None)
                        png_buffer.seek(0)
                        icon_img = Image.open(png_buffer).convert("RGBA")
                        if icon_img.mode == 'RGBA':
                            icon_img.putalpha(icon_img.convert("L"))
                        template.paste(icon_img, (int(ix), int(iy_p)), icon_img)
                    except Exception:
                        pass

            # Username
            user_txt = "@achadostecbra | Link na Bio"
            bbox = draw.textbbox((0, 0), user_txt, font=font_footer)
            tw = bbox[2] - bbox[0]
            # No Feed, sobe o username para não deixar um buraco. Mudado para Branco para máximo contraste.
            uy = footer_y + 195 if mode == "story" else footer_y + 65
            draw.text(((width - tw) / 2, uy), user_txt, font=font_footer, fill="#FFFFFF")

            template.save(output_path, quality=95)
            return output_path
        except Exception as e:
            print(f"   [ImageGenerator] Erro: {e}")
            return None
