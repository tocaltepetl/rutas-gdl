#!/usr/bin/env python3
"""Compara la publicación de GTFS de Guadalajara con otras ciudades.

Lee el catálogo de Mobility Database (feeds_v2.csv) y escribe
public/data/comparativa.json con:

- México: todos los feeds GTFS / GTFS-RT agrupados por estado.
- Principales áreas metropolitanas de Latinoamérica (lista METROS).

Criterio de «vigente»: el feed GTFS no está «deprecated» en el catálogo y su
latest.zip (la última copia que guarda Mobility Database) tiene servicio que
llega hasta la fecha del corte o después, es decir, la fecha máxima entre
calendar.txt (end_date), calendar_dates.txt (date con exception_type=1) y
feed_info.txt (feed_end_date) es >= hoy. Solo se descargan los latest.zip de
feeds no deprecated de México y de las áreas de la lista (unas decenas) y se leen
en memoria, sin guardarlos en disco.

Además se agregan a mano feeds conocidos que no están en el catálogo (MANUALES):
hoy, el GTFS vigente de SETRAN Jalisco publicado en Ualabee. Van con
`en_catalogo: false` y cuentan en los totales de Guadalajara y Jalisco.

Uso: python3 -I scripts/comparativa_mdb.py [--sin-descargas]
Solo biblioteca estándar.
"""
import csv
import datetime as dt
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

CSV_URL = "https://files.mobilitydatabase.org/feeds_v2.csv"
SALIDA = Path(__file__).resolve().parent.parent / "public" / "data" / "comparativa.json"
UA = {"User-Agent": "rutas-gdl-comparativa/1.0"}

# (clave, nombre, país, regex sobre "subdivisión | municipio")
METROS = [
    ("gdl", "Guadalajara", "MX", r"^Jalisco \| (Guadalajara)?$"),
    ("cdmx", "Ciudad de México", "MX", r"Mexico City|Federal District|Ciudad de M"),
    ("mty", "Monterrey", "MX", r"Nuevo Le"),
    ("tol", "Toluca", "MX", r"\| Toluca"),
    ("bog", "Bogotá", "CO", r"Bogot"),
    ("med", "Medellín", "CO", r"Antioquia"),
    ("cal", "Cali", "CO", r"Valle del Cauca"),
    ("scl", "Santiago", "CL", r"Santiago"),
    ("sao", "São Paulo", "BR", r"Região Metropolitana de São Paulo"),
    ("rio", "Río de Janeiro", "BR", r"Região Metropolitana do Rio"),
    ("bhz", "Belo Horizonte", "BR", r"Belo Horizonte"),
    ("cwb", "Curitiba", "BR", r"Curitiba"),
    ("poa", "Porto Alegre", "BR", r"Porto Alegre"),
    ("for", "Fortaleza", "BR", r"Fortaleza|^Ceará"),
    ("bue", "Buenos Aires", "AR", r"^Buenos Aires"),
    ("lim", "Lima", "PE", r"^Lima"),
    ("uio", "Quito", "EC", r"Pichincha|Quito"),
    ("mvd", "Montevideo", "UY", r"Montevideo"),
    ("pty", "Panamá", "PA", r"Panam"),
    ("sjo", "San José (CR)", "CR", r"San Jos"),
]

# Feeds que no están en el catálogo de Mobility Database pero se conocen.
# SETRAN Jalisco anunció el 30-sep-2026 su GTFS vigente, alojado en Ualabee
# (sin feed_info ni licencia). Se descarga igual que los latest.zip.
MANUALES = [{
    "id": "setran-ualabee",
    "tipo": "gtfs",
    "pais": "MX",
    "estado": "Jalisco",
    "municipio": "Guadalajara",
    "proveedor": "Secretaría de Transporte de Jalisco (SETRAN), alojado en Ualabee",
    "nombre": "GTFS transporte público Jalisco",
    "oficial": True,
    "status": "active",
    "metro": "gdl",
    "url": "https://ualabee.com/api/v3/cities/35/gtfs-feeds/public",
    "anuncio": "https://setran.jalisco.gob.mx/prensa/notas-web/archivos-gtfs-del-transporte-publico",
    "nota": "No está en el catálogo de Mobility Database; fuente agregada a mano.",
}]


def bajar(url, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def fin_servicio(datos):
    """Fecha máxima de servicio (YYYYMMDD) en un GTFS, o None."""
    fechas = []
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
        nombres = {Path(n).name: n for n in z.namelist()}

        def filas(nombre):
            if nombre not in nombres:
                return []
            texto = z.read(nombres[nombre]).decode("utf-8-sig", "replace")
            return csv.DictReader(io.StringIO(texto))

        fechas += [f.get("end_date", "").strip() for f in filas("calendar.txt")]
        fechas += [f.get("date", "").strip() for f in filas("calendar_dates.txt")
                   if f.get("exception_type", "").strip() == "1"]
        fechas += [f.get("feed_end_date", "").strip() for f in filas("feed_info.txt")]
    fechas = [f for f in fechas if re.fullmatch(r"\d{8}", f)]
    return max(fechas) if fechas else None


def main():
    descargar = "--sin-descargas" not in sys.argv
    hoy = dt.date.today()
    hoy_s = hoy.strftime("%Y%m%d")
    filas = list(csv.DictReader(io.StringIO(bajar(CSV_URL).decode("utf-8-sig"))))

    def metro_de(f):
        lugar = f"{f['location.subdivision_name']} | {f['location.municipality']}"
        for clave, _, pais, rx in METROS:
            if f["location.country_code"] == pais and re.search(rx, lugar):
                return clave
        return None

    feeds = []
    if True:  # los zip se leen en memoria; no se guarda nada en disco
        for f in filas:
            if f["data_type"] not in ("gtfs", "gtfs_rt"):
                continue
            metro = metro_de(f)
            if f["location.country_code"] != "MX" and not metro:
                continue
            reg = {
                "id": f["id"],
                "tipo": f["data_type"],
                "pais": f["location.country_code"],
                "estado": f["location.subdivision_name"],
                "municipio": f["location.municipality"],
                "proveedor": f["provider"],
                "nombre": f["name"],
                "oficial": {"True": True, "False": False}.get(f["is_official"]),
                "status": f["status"] or None,
                "metro": metro,
                "fin_servicio": None,
                "vigente": None,
                "en_catalogo": True,
            }
            if f["data_type"] == "gtfs" and f["status"] != "deprecated" and f["urls.latest"] and descargar:
                try:
                    fin = fin_servicio(bajar(f["urls.latest"]))
                    reg["fin_servicio"] = fin and f"{fin[:4]}-{fin[4:6]}-{fin[6:]}"
                    reg["vigente"] = bool(fin and fin >= hoy_s)
                except Exception as e:  # zip roto o no disponible
                    print(f"aviso: {f['id']}: {e}", file=sys.stderr)
            elif f["data_type"] == "gtfs":
                reg["vigente"] = False if f["status"] == "deprecated" else None
            feeds.append(reg)
        for m in MANUALES:
            reg = {**m, "fin_servicio": None, "vigente": None, "en_catalogo": False}
            if descargar:
                try:
                    fin = fin_servicio(bajar(m["url"], timeout=300))
                    reg["fin_servicio"] = fin and f"{fin[:4]}-{fin[4:6]}-{fin[6:]}"
                    reg["vigente"] = bool(fin and fin >= hoy_s)
                except Exception as e:
                    print(f"aviso: {m['id']}: {e}", file=sys.stderr)
            feeds.append(reg)

    def resumen(grupo):
        g = [x for x in grupo if x["tipo"] == "gtfs"]
        rt = [x for x in grupo if x["tipo"] == "gtfs_rt"]
        return {
            "gtfs": len(g),
            "gtfs_oficiales": sum(1 for x in g if x["oficial"]),
            "gtfs_activos": sum(1 for x in g if x["status"] == "active"),
            "gtfs_vigentes": sum(1 for x in g if x["vigente"]),
            "fin_servicio_max": max((x["fin_servicio"] for x in g if x["fin_servicio"]), default=None),
            "gtfs_fuera_catalogo": sum(1 for x in g if not x["en_catalogo"]),
            "gtfs_rt": len(rt),
            "gtfs_rt_activos": sum(1 for x in rt if x["status"] != "deprecated"),
            "feeds": [x["id"] for x in grupo],
        }

    metros = []
    for clave, nombre, pais, _ in METROS:
        r = {"clave": clave, "nombre": nombre, "pais": pais}
        r.update(resumen([x for x in feeds if x["metro"] == clave]))
        metros.append(r)
    estados = {}
    for x in feeds:
        if x["pais"] == "MX":
            estados.setdefault(x["estado"] or "(sin estado)", []).append(x)
    mexico = [{"estado": e, **resumen(v)} for e, v in sorted(estados.items())]

    SALIDA.write_text(json.dumps({
        "fuente": "Mobility Database (MobilityData), feeds_v2.csv, más fuentes manuales fuera del catálogo (en_catalogo: false)",
        "fuente_url": CSV_URL,
        "corte": hoy.isoformat(),
        "criterio_vigente": ("GTFS no deprecated cuyo latest.zip tiene servicio (calendar end_date, "
                             "calendar_dates con exception_type=1 o feed_end_date) hasta la fecha del corte o después"),
        "metros": metros,
        "mexico_por_estado": mexico,
        "feeds": [x for x in feeds if x["pais"] == "MX" or x["metro"]],
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"escrito {SALIDA} ({len(feeds)} feeds)")


if __name__ == "__main__":
    main()
