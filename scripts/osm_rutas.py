#!/usr/bin/env python3
"""Completa el mapa con rutas de OpenStreetMap que no están en el GTFS oficial.

Uso:
  python3 -I scripts/osm_rutas.py <carpeta_gtfs> public/data [--cache osm.json]

Consulta Overpass (relaciones route=bus/tram/light_rail/subway con geometría en
la zona metropolitana) y genera:
  public/data/rutas_osm.geojson  rutas cuyo `ref` no existe en el GTFS, más las
                                 del GTFS sin trazo que sí tienen trazo en OSM
  datos/comparacion-osm.md       reporte de la comparación
Los datos de OSM son © colaboradores de OpenStreetMap, bajo ODbL; el GeoJSON
derivado se publica bajo la misma licencia.

Con --cache se guarda la respuesta de Overpass (o se reutiliza si ya existe),
para no repetir la consulta.
"""
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

OVERPASS = "https://overpass-api.de/api/interpreter"
UA = "rutas-gdl/0.1"
BBOX = "20.50,-103.55,20.80,-103.20"
TOL = 0.00003  # igual que gtfs_a_geojson.py
CONSULTA = f"""[out:json][timeout:240];
relation["type"="route"]["route"~"^(bus|tram|light_rail|subway)$"]({BBOX});
out body geom meta;"""
TIPOS = {"tram": 0, "light_rail": 0, "subway": 1, "bus": 3}
NO_TRAZO = {"platform", "stop", "route_marker"}  # roles de ways que no son el recorrido


def id_gtfs(ref, ids):
    """route_id del GTFS que corresponde a un `ref` de OSM, o None.
    OSM usa TL-1 (tren ligero) y ST-L1 (SiTren) donde el GTFS usa MT_L1 y ST_L1."""
    if ref in ids:
        return ref
    por_corto = [i for i, r in ids.items() if r["route_short_name"] == ref]
    if len(por_corto) == 1:
        return por_corto[0]
    m = re.fullmatch(r"(TL|ST)-L?(\d+[A-Z]?)", ref)
    if m:
        cand = ("MT_L" if m[1] == "TL" else "ST_L") + m[2]
        return cand if cand in ids else None
    return None


def leer(carpeta, nombre):
    with open(Path(carpeta) / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def simplificar(pts, tol=TOL):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norma = (dx * dx + dy * dy) ** 0.5 or 1e-12
    dmax, imax = 0.0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / norma
        if d > dmax:
            dmax, imax = d, i
    if dmax <= tol:
        return [pts[0], pts[-1]]
    return simplificar(pts[: imax + 1], tol)[:-1] + simplificar(pts[imax:], tol)


def consultar(cache):
    if cache and Path(cache).exists():
        return json.loads(Path(cache).read_text(encoding="utf-8"))
    datos = urllib.parse.urlencode({"data": CONSULTA}).encode()
    req = urllib.request.Request(OVERPASS, data=datos, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        crudo = r.read()
    if cache:
        Path(cache).write_bytes(crudo)
    return json.loads(crudo)


def ensamblar(ways):
    """Une las ways (listas de (lon, lat)) en el orden de la relación.
    Devuelve una lista de tramos; más de uno si no conectan."""
    tramos = []
    for w in ways:
        if len(w) < 2:
            continue
        if tramos:
            t = tramos[-1]
            if t[-1] == w[0]:
                t.extend(w[1:]); continue
            if t[-1] == w[-1]:
                t.extend(w[-2::-1]); continue
            # el primer tramo quizá iba al revés
            if len(tramos) == 1 and t[0] in (w[0], w[-1]):
                t.reverse()
                t.extend(w[1:] if t[-1] == w[0] else w[-2::-1]); continue
        tramos.append(list(w))
    return tramos


def agencia_de(tags, agencias):
    red = tags.get("network", "")
    if red.startswith("Mi Macro") or red == "Macrobús":
        return "Mi Macro"
    if red in agencias:
        return red
    return None  # p. ej. el tren del zoológico: no es transporte público


def nombre_y_destino(tags):
    nombre = tags.get("name", "")
    base, _, dest = nombre.partition(": ")
    return (base or nombre), (tags.get("to") or dest)


def main(gtfs, salida, cache=None):
    sys.setrecursionlimit(20000)
    salida = Path(salida)
    raiz = Path(__file__).resolve().parent.parent
    agencias = {a["agency_name"] for a in leer(gtfs, "agency.txt")}
    ag_id = {a["agency_id"]: a["agency_name"] for a in leer(gtfs, "agency.txt")}
    gtfs_rutas = {r["route_id"]: r for r in leer(gtfs, "routes.txt")}
    con_trazo = {f["properties"]["id"] for f in
                 json.loads((salida / "rutas.geojson").read_text(encoding="utf-8"))["features"]}
    sin_trazo = set(gtfs_rutas) - con_trazo

    osm = consultar(cache)
    base_osm = osm.get("osm3s", {}).get("timestamp_osm_base", "")
    por_ref = defaultdict(list)
    descartadas = []
    for e in osm["elements"]:
        if e.get("type") != "relation":
            continue
        t = e.get("tags", {})
        ref = (t.get("ref") or "").strip()
        ag = agencia_de(t, agencias)
        if not ref or not ag:
            descartadas.append((e["id"], t.get("name", "(sin nombre)"), "sin ref" if not ref else "red no reconocida"))
            continue
        por_ref[ref].append((e, ag))

    feats, nuevas, completadas, sin_geom = [], [], [], []
    hoy = date.today()
    for ref in sorted(por_ref, key=lambda s: (s[0], len(s), s)):
        gid = id_gtfs(ref, gtfs_rutas)
        if gid and gid not in sin_trazo:
            continue
        rels = sorted(por_ref[ref], key=lambda x: x[0]["id"])
        g = gtfs_rutas.get(gid)
        fechas = []
        for sentido, (e, ag) in enumerate(rels):
            t = e["tags"]
            ways = [[(p["lon"], p["lat"]) for p in m["geometry"]]
                    for m in e.get("members", [])
                    if m["type"] == "way" and m.get("role", "") not in NO_TRAZO and m.get("geometry")]
            tramos = [[[round(x, 5), round(y, 5)] for x, y in simplificar(tr)]
                      for tr in ensamblar(ways)]
            tramos = [tr for tr in tramos if len(tr) > 1]
            if not tramos:
                continue
            nombre, destino = nombre_y_destino(t)
            editado = e.get("timestamp", "")[:10]
            fechas.append(editado)
            geom = ({"type": "LineString", "coordinates": tramos[0]} if len(tramos) == 1
                    else {"type": "MultiLineString", "coordinates": tramos})
            color = t.get("colour", "")
            feats.append({"type": "Feature", "geometry": geom, "properties": {
                "id": gid or ref,
                "corto": g["route_short_name"] if g else ref,
                "nombre": g["route_long_name"] if g else nombre,
                "agencia": ag_id.get(g["agency_id"], ag) if g else ag,
                "tipo": int(g["route_type"]) if g else TIPOS.get(t.get("route"), 3),
                "color": ("#" + g["route_color"]) if g and g.get("route_color") else
                         (color if color.startswith("#") and len(color) == 7 else "#666666"),
                "sentido": sentido,
                "destino": destino,
                "frec_min": None,
                "fuente": "osm",
                "osm_id": e["id"],
                "editado": editado,
                "completa_gtfs": bool(g),
            }})
        if fechas:
            (completadas if g else nuevas).append((ref, rels, min(fechas), max(fechas)))
        elif not g:
            sin_geom.append((ref, rels, "", max(e.get("timestamp", "")[:10] for e, _ in rels)))

    with open(salida / "rutas_osm.geojson", "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection",
                   "licencia": "ODbL 1.0 — © colaboradores de OpenStreetMap",
                   "fuente": f"Overpass API, base OSM {base_osm}",
                   "features": feats}, f, ensure_ascii=False, separators=(",", ":"))

    def antig(d):
        try:
            dias = (hoy - datetime.strptime(d, '%Y-%m-%d').date()).days
            return f"{dias // 365} años" if dias >= 365 else f"{dias // 30} meses"
        except ValueError:
            return "?"

    def fila(ref, rels, f0, f1):
        ids = ", ".join(f"[{e['id']}](https://www.openstreetmap.org/relation/{e['id']})" for e, _ in rels)
        nom = nombre_y_destino(rels[0][0]["tags"])[0]
        return f"| {ref} | {nom} | {ids} | {f1} | {antig(f1)} |"

    con_ref = {id_gtfs(r, gtfs_rutas) for r in por_ref}
    sin_osm = sorted(gtfs_rutas[i]["route_short_name"] for i in sin_trazo - con_ref)
    osm_sin_geom = sorted(gtfs_rutas[i]["route_short_name"] for i in sin_trazo & con_ref
                          if i not in {f["properties"]["id"] for f in feats})
    ultimas = sorted(e.get("timestamp", "")[:4] for v in por_ref.values() for e, _ in v)
    por_anio = defaultdict(int)
    for a in ultimas:
        por_anio[a] += 1
    md = [
        "# Comparación GTFS oficial vs. OpenStreetMap",
        "",
        f"Generado por `scripts/osm_rutas.py` el {hoy}, con datos OSM al {base_osm[:10]}.",
        "Datos OSM © colaboradores de OpenStreetMap, ODbL.",
        "",
        f"- Relaciones de ruta en OSM en la zona: {sum(len(v) for v in por_ref.values())}"
        f" ({len(por_ref)} `ref` distintos); descartadas: {len(descartadas)}.",
        f"- Rutas en el GTFS: {len(gtfs_rutas)}; con trazo: {len(gtfs_rutas) - len(sin_trazo)}; "
        f"sin trazo: {len(sin_trazo)}.",
        f"- Agregadas al mapa desde OSM: {len(nuevas)} nuevas y {len(completadas)} que completan "
        "rutas del GTFS sin trazo.",
        "",
        "La comparación es por `ref` exacto: `C12` en OSM no es `C12-V1` del GTFS. Algunas",
        "«nuevas» pueden ser la misma ruta con otra clave; conviene revisarlas a mano.",
        "",
        "## Rutas en OSM que no están en el GTFS",
        "",
        "| ref | nombre en OSM | relaciones | última edición | antigüedad |",
        "|---|---|---|---|---|",
        *[fila(*x) for x in nuevas],
        "",
        "## Rutas del GTFS sin trazo que sí están en OSM",
        "",
        "| ref | nombre en OSM | relaciones | última edición | antigüedad |",
        "|---|---|---|---|---|",
        *[fila(*x) for x in completadas],
        "",
        f"Están en OSM pero sin trazo (solo paradas): " + (", ".join(osm_sin_geom) or "ninguna") + ".",
        "",
        f"Siguen sin trazo en ninguna fuente ({len(sin_osm)}): " + (", ".join(sin_osm) or "ninguna") + ".",
        "",
        "## En OSM y no en el GTFS, pero sin trazo (solo paradas; no se muestran)",
        "",
        "| ref | nombre en OSM | relaciones | última edición | antigüedad |",
        "|---|---|---|---|---|",
        *[fila(*x) for x in sin_geom],
        "",
        "Muchas relaciones de la zona (importadas en 2022) solo tienen paradas, sin las",
        "calles del recorrido. Completarlas en OSM las haría aparecer aquí.",
        "",
        "## Antigüedad de las relaciones OSM (año de última edición)",
        "",
        *[f"- {a}: {n}" for a, n in sorted(por_anio.items())],
        "",
        "## Descartadas",
        "",
        *[f"- [{i}](https://www.openstreetmap.org/relation/{i}) {n} ({m})" for i, n, m in descartadas],
        "",
    ]
    (raiz / "datos").mkdir(exist_ok=True)
    (raiz / "datos" / "comparacion-osm.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(feats)} trazos OSM: {len(nuevas)} rutas nuevas, {len(completadas)} completan el GTFS")


if __name__ == "__main__":
    args = sys.argv[1:]
    cache = None
    if "--cache" in args:
        i = args.index("--cache")
        cache = args[i + 1]
        del args[i:i + 2]
    main(*args[:2], cache=cache)
