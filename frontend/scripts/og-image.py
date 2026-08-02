#!/usr/bin/env python3
"""Genera frontend/public/og.png, la imagen social por defecto del sitio.

El export estático no puede generar imágenes en tiempo de petición, así que la
tarjeta se versiona como PNG. Este script existe para que ese binario tenga
fuente: si cambia el texto o un token de color, se regenera aquí en lugar de
editarse a mano.

Colores: los tokens de src/lib/design-system/theme.ts (navy, offwhite,
terracotta, amber). Tipografía: IBM Plex, la misma familia que carga el
dashboard vía next/font.

Uso:

    pip install pillow
    # descargar IBM Plex (OFL) y apuntar --fonts a la carpeta con los .ttf
    python3 frontend/scripts/og-image.py --fonts /ruta/a/ttf

Se espera encontrar IBMPlexSerif-Bold.ttf, IBMPlexSerif-SemiBold.ttf,
IBMPlexSans-Regular.ttf e IBMPlexMono-Medium.ttf en esa carpeta.

Este script no forma parte de ninguna compuerta: nada lo ejecuta en CI.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# -- Tokens de src/lib/design-system/theme.ts --------------------------------
NAVY = (0x18, 0x22, 0x2D)
OFFWHITE = (0xF8, 0xF7, 0xF2)
TERRACOTTA = (0xB4, 0x47, 0x2D)
AMBER = (0xB7, 0x7A, 0x1E)

WIDTH, HEIGHT = 1200, 630
MARGIN = 80

# -- Texto. Todo proviene de copy real del sitio -----------------------------
# eyebrow: kicker de la portada (src/app/page.tsx, COPY.es.kicker)
EYEBROW = "MODELACIÓN ACTUARIAL EN CÓDIGO ABIERTO · MÉXICO"
# wordmark: hero_titulo (src/lib/i18n/translations.ts)
WORDMARK = "suite_actuarial"
# titular: title del layout raíz (src/app/layout.tsx)
HEADLINE = "Laboratorio actuarial abierto"
# cuerpo: description del layout raíz, partida en dos líneas
BODY = [
    "Modelos actuariales explicados y calculadoras reproducibles,",
    "con sus fuentes y sus límites, desde el mercado asegurador mexicano.",
]
# pie: las seis etapas de PROCESS.es (src/app/page.tsx)
STAGES = "PROPÓSITO · BENEFICIOS · SUPUESTOS · MÉTODO · RESULTADOS · VALIDACIÓN"
DOMAIN = "suite.gonor.me"


def mix(
    color: tuple[int, int, int], background: tuple[int, int, int], alpha: float
) -> tuple[int, int, int]:
    """Opacidad plana sobre el fondo; PIL no compone texto translúcido."""
    blend = [round(c * alpha + b * (1 - alpha)) for c, b in zip(color, background, strict=True)]
    return blend[0], blend[1], blend[2]


def tracked(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill,
    tracking: float,
) -> None:
    """Dibuja texto con interletraje; PIL no expone letter-spacing."""
    x, y = xy
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + tracking


def build(font_dir: Path, out: Path) -> None:
    def load(name: str, size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(font_dir / name), size)

    serif_bold = load("IBMPlexSerif-Bold.ttf", 96)
    serif_semi = load("IBMPlexSerif-SemiBold.ttf", 44)
    sans = load("IBMPlexSans-Regular.ttf", 26)
    mono_small = load("IBMPlexMono-Medium.ttf", 18)
    mono_tiny = load("IBMPlexMono-Medium.ttf", 15)

    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)

    # Filete dorado superior, el mismo recurso que cierra el Footer.
    draw.rectangle([0, 0, WIDTH, 7], fill=AMBER)

    y = 96
    tracked(draw, (MARGIN, y), EYEBROW, mono_tiny, AMBER, tracking=1.6)

    y += 54
    draw.text((MARGIN, y), WORDMARK, font=serif_bold, fill=OFFWHITE)

    y += 132
    draw.rectangle([MARGIN, y, MARGIN + 104, y + 5], fill=TERRACOTTA)

    y += 40
    draw.text((MARGIN, y), HEADLINE, font=serif_semi, fill=OFFWHITE)

    y += 76
    body_color = mix(OFFWHITE, NAVY, 0.72)
    for line in BODY:
        draw.text((MARGIN, y), line, font=sans, fill=body_color)
        y += 38

    # Pie: filete fino y una línea de referencia.
    rule_y = HEIGHT - 96
    draw.rectangle([MARGIN, rule_y, WIDTH - MARGIN, rule_y], fill=mix(OFFWHITE, NAVY, 0.18))

    foot_y = rule_y + 30
    draw.text((MARGIN, foot_y), DOMAIN, font=mono_small, fill=mix(OFFWHITE, NAVY, 0.55))

    tracking = 1.2
    stages_width = sum(draw.textlength(c, font=mono_tiny) + tracking for c in STAGES) - tracking
    tracked(
        draw,
        (round(WIDTH - MARGIN - stages_width), foot_y + 3),
        STAGES,
        mono_tiny,
        mix(OFFWHITE, NAVY, 0.42),
        tracking=tracking,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, "PNG", optimize=True)
    print(f"escrito {out} ({out.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fonts", required=True, type=Path, help="carpeta con los .ttf de IBM Plex"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "public" / "og.png",
        help="ruta de salida del PNG",
    )
    args = parser.parse_args()
    build(args.fonts, args.out)


if __name__ == "__main__":
    main()
