#!/usr/bin/env python3
"""Estado del GTFS oficial de Guadalajara en la Mobility Database (MDB).

Genera public/data/mdb.json con: estado del feed mdb-2366 en el catálogo
público (feeds_v2.csv), vigencia del calendario (de latest.zip), días desde
que venció, fecha y hash de la última versión del zip, URL de origen y si el
portal de datos.jalisco.gob.mx responde. Solo usa la biblioteca estándar y
fuentes públicas sin token.

    python3 -I scripts/mdb_estado.py [salida.json]

Además imprime en stdout líneas `clave=valor` para GitHub Actions
(feeds_nuevos, version) y deja la lista de feeds en el JSON.
"""
import csv
import datetime as dt
import email.utils
import io
import json
import pathlib
import sys
import urllib.error
import urllib.request
import zipfile

FEED = "mdb-2366"
CATALOGO = "https://files.mobilitydatabase.org/feeds_v2.csv"
ZIP = f"https://files.mobilitydatabase.org/{FEED}/latest.zip"
PAGINA = f"https://mobilitydatabase.org/feeds/gtfs/{FEED}"
CONOCIDOS = {"mdb-1925", "mdb-1926", "mdb-2034", "mdb-2366"}
UA = {"User-Agent": "rutas-gdl-monitor (+https://github.com/tocaltepetl/rutas-gdl)"}
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def pedir(url, metodo="GET", timeout=60):
    req = urllib.request.Request(url, headers=UA, method=metodo)
    return urllib.request.urlopen(req, timeout=timeout)


def catalogo():
    with pedir(CATALOGO) as r:
        texto = r.read().decode("utf-8-sig")
    filas = list(csv.DictReader(io.StringIO(texto)))
    propia = next(f for f in filas if f["id"] == FEED)

    def es_gdl(f):
        campos = " ".join(f.get(k, "") for k in (
            "location.subdivision_name", "location.municipality", "provider", "name"))
        return f.get("location.country_code") == "MX" and (
            "jalisco" in campos.lower() or "guadalajara" in campos.lower())

    gdl = [{"id": f["id"], "tipo": f["data_type"], "nombre": f["name"],
            "proveedor": f["provider"], "estado": f["status"]}
           for f in filas if es_gdl(f)]
    return propia, gdl


def vigencia(datos):
    """min start_date / max end_date de calendar.txt y calendar_dates.txt."""
    fechas = []
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
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


def portal_responde(url):
    try:
        with pedir(url, "HEAD", timeout=20) as r:
            return r.status < 400
    except (urllib.error.URLError, OSError, ValueError):
        return False


def main():
    salida = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "public/data/mdb.json"
    hoy = dt.date.today()
    propia, gdl = catalogo()

    with pedir(ZIP) as r:
        datos = r.read()
        cab = r.headers
    md5 = next((h.split("=", 1)[1] for h in cab.get_all("x-goog-hash") or []
                if h.startswith("md5=")), None)
    modificado = cab.get("Last-Modified")
    if modificado:
        modificado = email.utils.parsedate_to_datetime(modificado).date().isoformat()
    inicio, fin = vigencia(datos)
    origen = propia["urls.direct_download"]

    estado = {
        "feed": FEED,
        "pagina": PAGINA,
        "estado_mdb": propia["status"],
        "redirige_a": propia.get("redirect.id") or None,
        "proveedor": propia["provider"],
        "url_origen": origen,
        "portal_responde": portal_responde(origen),
        "copia_mdb": ZIP,
        "version": {"fecha": modificado, "md5": md5,
                    "generacion": cab.get("x-goog-generation"), "bytes": len(datos)},
        "calendario": {"inicio": inicio and inicio.isoformat(),
                       "fin": fin and fin.isoformat()},
        "dias_desde_vencimiento": (hoy - fin).days if fin and fin < hoy else 0,
        "validador": None,  # el reporte del validador solo está en la API (requiere token)
        "feeds_gdl": gdl,
        "revisado": hoy.isoformat(),
    }
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    nuevos = [f["id"] for f in gdl if f["id"] not in CONOCIDOS]
    print(f"feeds_nuevos={','.join(nuevos)}")
    print(f"version={estado['version']['generacion'] or ''}")


if __name__ == "__main__":
    main()
