#!/usr/bin/env python3
"""Estado del GTFS vigente que SETRAN Jalisco publica a través de Ualabee.

SETRAN anunció el 2026-09-30 que su GTFS está en
https://ualabee.com/api/v3/cities/35/gtfs-feeds/public, que redirige (302)
a platform.ualabee.com y de ahí a Firebase Storage con un token de descarga
en la URL. Este script sigue los redirects, y sin descargar los ~52 MB
completos (peticiones HTTP Range) lee del ZIP: tamaño, fecha de modificación,
MD5, fechas de los archivos internos y min/max del calendario
(calendar.txt y calendar_dates.txt). Si el servidor no acepta Range, descarga
el ZIP completo.

NO guarda las URL de redirección: llevan tokens. Solo se guarda el host
final. Solo biblioteca estándar.

    python3 -I scripts/setran_estado.py [salida.json]

Genera public/data/setran.json e imprime en stdout líneas `clave=valor` para
GitHub Actions: setran_ok (si|no), setran_fin (AAAA-MM-DD), setran_dias
(días hasta el fin del calendario; negativo si venció), setran_error.
"""
import csv
import datetime as dt
import email.utils
import io
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ENLACE = "https://ualabee.com/api/v3/cities/35/gtfs-feeds/public"
NOTA = "https://setran.jalisco.gob.mx/prensa/notas-web/archivos-gtfs-del-transporte-publico"
UA = {"User-Agent": "rutas-gdl-monitor (+https://github.com/tocaltepetl/rutas-gdl)"}
RAIZ = pathlib.Path(__file__).resolve().parent.parent


class ZipRemoto:
    """Archivo de solo lectura sobre HTTP Range, para zipfile.

    Pide bloques de al menos 64 KB y guarda el último para no hacer una
    petición por cada cabecera pequeña."""

    BLOQUE = 1 << 16

    def __init__(self, url, tam):
        self.url, self.tam, self.pos, self.pedido = url, tam, 0, 0
        self.cache_ini, self.cache = 0, b""

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.tam + off}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.tam - self.pos
        n = min(n, self.tam - self.pos)
        if n <= 0:
            return b""
        fin_cache = self.cache_ini + len(self.cache)
        if not (self.cache_ini <= self.pos and self.pos + n <= fin_cache):
            fin = min(self.tam, self.pos + max(n, self.BLOQUE)) - 1
            req = urllib.request.Request(
                self.url, headers={**UA, "Range": f"bytes={self.pos}-{fin}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status != 206:
                    raise OSError("el servidor no respetó Range")
                self.cache_ini, self.cache = self.pos, r.read()
            self.pedido += len(self.cache)
        i = self.pos - self.cache_ini
        datos = self.cache[i:i + n]
        self.pos += len(datos)
        return datos


def vigencia(z):
    fechas = []
    nombres = {pathlib.PurePosixPath(n).name: n for n in z.namelist()}
    for archivo, cols in (("calendar.txt", ("start_date", "end_date")),
                          ("calendar_dates.txt", ("date",))):
        if archivo not in nombres:
            continue
        with z.open(nombres[archivo]) as f:
            for fila in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                for c in cols:
                    v = (fila.get(c) or "").strip()
                    if len(v) == 8 and v.isdigit():
                        fechas.append(dt.date(int(v[:4]), int(v[4:6]), int(v[6:])))
    if not fechas:
        return None, None
    return min(fechas), max(fechas)


def revisar():
    # HEAD siguiendo redirects; solo nos quedamos con el host final.
    req = urllib.request.Request(ENLACE, headers=UA, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        final, cab = r.geturl(), r.headers
    tam = int(cab.get("Content-Length") or 0)
    rango = cab.get("Accept-Ranges", "").lower() == "bytes" and tam > 0
    if rango:
        fuente = ZipRemoto(final, tam)
        z = zipfile.ZipFile(fuente)
    else:
        with urllib.request.urlopen(urllib.request.Request(final, headers=UA), timeout=300) as r:
            datos = r.read()
        tam, fuente = len(datos), None
        z = zipfile.ZipFile(io.BytesIO(datos))
    with z:
        archivos = sorted(
            ({"nombre": i.filename, "fecha": dt.datetime(*i.date_time).date().isoformat(),
              "bytes": i.file_size} for i in z.infolist() if not i.is_dir()),
            key=lambda a: a["nombre"])
        inicio, fin = vigencia(z)
    modificado = cab.get("Last-Modified")
    if modificado:
        modificado = email.utils.parsedate_to_datetime(modificado).date().isoformat()
    md5 = next((h.split("=", 1)[1] for h in cab.get_all("x-goog-hash") or []
                if h.startswith("md5=")), None)
    nombres = {pathlib.PurePosixPath(a["nombre"]).name for a in archivos}
    return {
        "host_final": urllib.parse.urlsplit(final).hostname,
        "version": {"fecha": modificado, "md5": md5,
                    "generacion": cab.get("x-goog-generation"), "bytes": tam},
        "descargado_bytes": fuente.pedido if fuente else tam,
        "archivos": archivos,
        "feed_info": "feed_info.txt" in nombres,
        "calendario": {"inicio": inicio and inicio.isoformat(),
                       "fin": fin and fin.isoformat()},
    }


def main():
    salida = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "public/data/setran.json"
    hoy = dt.date.today()
    estado = {"enlace": ENLACE, "anuncio": NOTA, "proveedor": "Ualabee",
              "licencia": None, "ok": False, "error": None}
    try:
        estado.update(revisar())
        estado["ok"] = True
    except (urllib.error.URLError, OSError, ValueError, zipfile.BadZipFile) as e:
        # Sin URL en el mensaje: podría traer el token.
        estado["error"] = type(e).__name__ + (f" {e.code}" if isinstance(e, urllib.error.HTTPError) else "")
    fin = (estado.get("calendario") or {}).get("fin")
    dias = (dt.date.fromisoformat(fin) - hoy).days if fin else None
    estado["dias_para_vencer"] = dias
    estado["revisado"] = hoy.isoformat()
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"setran_ok={'si' if estado['ok'] else 'no'}")
    print(f"setran_fin={fin or ''}")
    print(f"setran_dias={'' if dias is None else dias}")
    print(f"setran_error={estado['error'] or ''}")


if __name__ == "__main__":
    main()
