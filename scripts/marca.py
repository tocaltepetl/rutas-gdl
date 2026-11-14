"""Genera la marca de rutas-gdl (familia tocaltepetl): cerro + agua + glifo de ruta.

Uso: venv/bin/python tools/marca.py <Bricolage.ttf> <carpeta_salida>
"""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

TINTA, PAPEL, AGUA, VERDE, TERRA = "#1d2420", "#efe9dc", "#3f86a8", "#2f6b4f", "#b5532c"

# Glifo: una ruta en zigzag (terracota) con cuatro paradas (verde), dentro del arco.
PUNTOS = [(36, 68), (44, 57), (54, 63), (63, 51)]


def glifo(parada_borde):
    d = "M" + " L".join(f"{x} {y}" for x, y in PUNTOS)
    paradas = "".join(
        f'<circle cx="{x}" cy="{y}" r="4.2" fill="{VERDE}" stroke="{parada_borde}" stroke-width="1.6"/>'
        for x, y in PUNTOS)
    return (f'<path d="{d}" fill="none" stroke="{TERRA}" stroke-width="5" '
            f'stroke-linecap="round" stroke-linejoin="round"/>{paradas}')


def icono(tinta, borde):
    """Ícono 100×100 con trazo de cerro y doble ola (como los logos de la familia)."""
    return (f'<g transform="translate(9 20) scale(.82)">'
            f'<path d="M20 72 C20 42 31 10 50 10 C69 10 80 42 80 72" fill="none" stroke="{tinta}" stroke-width="10.5" stroke-linecap="round"/>'
            f'<g fill="none" stroke="{AGUA}" stroke-linecap="round">'
            f'<path d="M12 80 q9.5 -6 19 0 t19 0 t19 0 t19 0" stroke-width="5"/>'
            f'<path d="M22 91 q7 -5 14 0 t14 0 t14 0 t14 0" stroke-width="4"/></g></g>'
            f'{glifo(borde)}')


def favicon():
    """Favicon: trazos más gruesos, una sola ola, se adapta a modo oscuro."""
    pts = " L".join(f"{x} {y}" for x, y in PUNTOS)
    paradas = "".join(f'<circle class="p" cx="{x}" cy="{y}" r="5"/>' for x, y in PUNTOS)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<style>.c{{stroke:{TINTA}}}.p{{fill:{VERDE};stroke:{PAPEL};stroke-width:1.8}}'
            f'@media (prefers-color-scheme:dark){{.c{{stroke:{PAPEL}}}.p{{stroke:{TINTA}}}}}</style>'
            '<g transform="translate(5 22) scale(.86)">'
            '<path class="c" d="M20 72 C20 42 31 10 50 10 C69 10 80 42 80 72" fill="none" stroke-width="14" stroke-linecap="round"/>'
            f'<path d="M12 88 q9.5 -7 19 0 t19 0 t19 0 t19 0" fill="none" stroke="{AGUA}" stroke-width="9" stroke-linecap="round"/></g>'
            f'<path d="M{pts}" fill="none" stroke="{TERRA}" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'{paradas}</svg>')


class Texto:
    def __init__(self, ttf, peso):
        f = TTFont(ttf)
        self.f = instantiateVariableFont(f, {"wght": peso, "opsz": 48, "wdth": 100})
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm

    def path(self, texto, x, y_base, tam):
        """Devuelve (d, ancho) del texto convertido a trazos."""
        esc = tam / self.upm
        pen = SVGPathPen(self.gs)
        cur = 0
        for ch in texto:
            g = self.cmap[ord(ch)]
            self.gs[g].draw(TransformPen(pen, (esc, 0, 0, -esc, x + cur * esc, y_base)))
            cur += self.gs[g].width
        return pen.getCommands(), cur * esc


def main(ttf, salida):
    out = Path(salida)
    out.mkdir(parents=True, exist_ok=True)
    negrita = Texto(ttf, 700)
    media = Texto(ttf, 500)
    svg = lambda vb, body: f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">{body}</svg>\n'

    (out / "rutas-gdl.svg").write_text(svg("0 0 100 100", icono(TINTA, PAPEL)))
    (out / "rutas-gdl-claro.svg").write_text(svg("0 0 100 100", icono(PAPEL, TINTA)))
    (out / "rutas-gdl-favicon.svg").write_text(favicon() + "\n")

    for nombre, tinta, borde in (("rutas-gdl-horizontal", TINTA, PAPEL), ("rutas-gdl-horizontal-claro", PAPEL, TINTA)):
        d, ancho = negrita.path("rutas gdl", 118, 68, 54)
        body = (f'<svg x="0" y="0" width="100" height="100" viewBox="0 0 100 100">{icono(tinta, borde)}</svg>'
                f'<path d="{d}" fill="{tinta}"/>')
        (out / f"{nombre}.svg").write_text(svg(f"0 0 {int(118 + ancho + 12)} 100", body))

    # Imagen para compartir (Open Graph), 1200×630, fondo tinta.
    d1, _ = negrita.path("rutas gdl", 380, 300, 112)
    d2, _ = media.path("Observatorio de las rutas de transporte", 384, 380, 38)
    d3, _ = media.path("público de Guadalajara, con datos abiertos", 384, 428, 38)
    d4, _ = media.path("rutasgdl.tocaltepetl.org", 384, 520, 30)
    og = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">'
          f'<rect width="1200" height="630" fill="{TINTA}"/>'
          f'<svg x="80" y="160" width="260" height="260" viewBox="0 0 100 100">{icono(PAPEL, TINTA)}</svg>'
          f'<path d="{d1}" fill="{PAPEL}"/><path d="{d2}{d3}" fill="{PAPEL}" opacity=".85"/>'
          f'<path d="{d4}" fill="{AGUA}"/></svg>\n')
    (out / "og-fuente.svg").write_text(og)
    print("listo:", ", ".join(sorted(p.name for p in out.iterdir())))


if __name__ == "__main__":
    main(*sys.argv[1:3])
