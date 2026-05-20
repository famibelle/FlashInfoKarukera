#!/usr/bin/env python3
"""
Script pour redimensionner une image (par défaut docs/artwork.jpg) aux dimensions Apple Podcasts.

Usage:
    python resize_artwork.py
    python resize_artwork.py --input docs/artwork.jpg --output docs/artwork.jpg
    python resize_artwork.py -i input.png -o output.jpg --size 3000 3000 --quality 90

Nécessite Pillow : pip install pillow
"""

import argparse
from PIL import Image, ImageOps
import os


def main():
    parser = argparse.ArgumentParser(
        description="Redimensionne une image aux dimensions Apple Podcasts (3000x3000 par défaut).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python resize_artwork.py                          # Utilise les valeurs par défaut
  python resize_artwork.py -i docs/artwork.png      # Fichier d'entrée personnalisé
  python resize_artwork.py -o docs/artwork_3k.jpg   # Fichier de sortie personnalisé
  python resize_artwork.py --size 1400 1400        # Taille personnalisée
  python resize_artwork.py --quality 85             # Qualité JPG personnalisée
        """
    )
    parser.add_argument(
        "-i", "--input",
        default="docs/artwork.jpg",
        help="Chemin du fichier image d'entrée (par défaut : docs/artwork.jpg)"
    )
    parser.add_argument(
        "-o", "--output",
        default="docs/artwork.jpg",
        help="Chemin du fichier image de sortie (par défaut : docs/artwork.jpg, écrase l'origine)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=3000,
        help="Largeur de sortie en pixels (par défaut : 3000)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=3000,
        help="Hauteur de sortie en pixels (par défaut : 3000)"
    )
    parser.add_argument(
        "--size",
        type=int,
        nargs=2,
        metavar=("WIDTH", "HEIGHT"),
        help="Largeur et hauteur de sortie en pixels (remplace --width et --height)"
    )
    parser.add_argument(
        "--format",
        default="JPEG",
        choices=["JPEG", "PNG"],
        help="Format de sortie (par défaut : JPEG)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="Qualité de compression (1-100, par défaut : 95)"
    )
    
    args = parser.parse_args()
    
    # Si --size est fourni, il prend la priorité
    if args.size:
        width, height = args.size
    else:
        width, height = args.width, args.height
    
    TARGET_SIZE = (width, height)
    FORMAT = args.format
    QUALITY = args.quality
    input_path = args.input
    output_path = args.output

    # Vérification
    if not os.path.exists(input_path):
        print(f"❌ Erreur : {input_path} introuvable.")
        exit(1)

    # Ouverture
    img = Image.open(input_path)
    print(f"📄 Image originale : {img.size} pixels, mode={img.mode}, format={img.format}")

    # Conversion RVB si nécessaire (sauf pour PNG qui peut garder RGBA)
    if img.mode != "RGB" and FORMAT == "JPEG":
        img = img.convert("RGB")
        print("🎨 Converti en RVB.")

    # Redimensionnement avec padding (pour garder les proportions)
    img_resized = ImageOps.fit(img, TARGET_SIZE, method=Image.Resampling.LANCZOS, bleed=0.0, centering=(0.5, 0.5))
    print(f"✅ Redimensionné à {TARGET_SIZE} pixels (avec padding si nécessaire).")

    # Sauvegarde
    save_kwargs = {"quality": QUALITY} if FORMAT == "JPEG" else {}
    img_resized.save(output_path, format=FORMAT, **save_kwargs)
    print(f"💾 Sauvegardé en {FORMAT} (qualité={QUALITY}) : {output_path}")
    print("✨ Fait ! Vérifiez le fichier avant de le déployer.")


if __name__ == "__main__":
    main()
