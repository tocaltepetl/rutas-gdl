#!/usr/bin/env python3
"""Convierte el GTFS de SETRAN Jalisco en GeoJSON ligero para el mapa.

Uso: python3 -I scripts/gtfs_a_geojson.py <carpeta_gtfs_descomprimida> public/data [datos/lineas-treep-mi-transporte.txt]

Fuente actual: GTFS estatal que SETRAN publica en Ualabee
(https://ualabee.com/api/v3/cities/35/gtfs-feeds/public). Trae también Puerto
Vallarta, Lagos de Moreno y Tepatitlán: solo se usan las agencias del Área
Metropolitana de Guadalajara (AGENCIAS_AMG). `frec_min` se deja en null aquí y
lo llena scripts/analisis.py (que calcula las frecuencias desde stop_times).

Genera:
  rutas.geojson   una línea por ruta y sentido (trazo del shape), con propiedades
  paradas.geojson paradas con la lista de rutas que pasan por ellas
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

TOL = 0.00003  # ~3 m: tolerancia de simplificación (Douglas-Peucker)
# Agencias del AMG. Fuera: PV y PVMT (Puerto Vallarta), LGM (Lagos de Moreno) y
# TEP (Tepabus, Tepatitlán): sus paradas están a 60-200 km de Guadalajara.
AGENCIAS_AMG = {"BUS", "MM", "MMA", "MMP", "MT", "ST", "ME"}


def corto(r):
    """Nombre corto limpio: el feed 2026 trae espacios ('T01 ') y vacíos (MC-L1E)."""
    return (r["route_short_name"] or "").strip() or r["route_id"]


def largo(r):
    """El feed 2026 deja route_long_name vacío y pone el nombre en route_desc."""
    return (r.get("route_long_name") or "").strip() or (r.get("route_desc") or "").strip()


def filas(carpeta, nombre):
    """Lee un CSV renglón por renglón (stop_times.txt pesa ~360 MB)."""
    with open(Path(carpeta) / nombre, encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


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


def main(gtfs, salida, vigentes=None):
    """`vigentes`: archivo con identificadores de líneas de Mi Transporte
    actuales (uno por renglón, # = comentario). Las líneas de Mi Transporte
    del GTFS que no estén ahí se marcan con `revisar: true`."""
    lista = None
    if vigentes:
        with open(vigentes, encoding="utf-8") as f:
            lista = {l.strip() for l in f if l.strip() and not l.startswith("#")}
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    sys.setrecursionlimit(20000)

    agencias = {a["agency_id"]: a["agency_name"] for a in leer(gtfs, "agency.txt")}
    rutas = {r["route_id"]: r for r in leer(gtfs, "routes.txt") if r["agency_id"] in AGENCIAS_AMG}

    puntos = defaultdict(list)
    for p in filas(gtfs, "shapes.txt"):
        puntos[p["shape_id"]].append(
            (int(p["shape_pt_sequence"]), float(p["shape_pt_lon"]), float(p["shape_pt_lat"]))
        )

    # un shape por (ruta, sentido); y viajes representativos para paradas
    vistos = {}
    viaje_rep = {}
    for t in filas(gtfs, "trips.txt"):
        if t["route_id"] not in rutas:
            continue
        clave = (t["route_id"], t.get("direction_id") or "0", t["shape_id"])
        vistos.setdefault(clave, (t.get("trip_headsign") or "").strip())
        viaje_rep.setdefault(clave, t["trip_id"])

    feats = []
    for (rid, sentido, sid), destino in sorted(vistos.items()):
        r = rutas.get(rid)
        if not r or sid not in puntos:
            continue
        # Respeta el orden del archivo y parte el trazo donde la secuencia
        # reinicia: T14B_r1 (GTFS 2024) trae dos tramos con secuencias
        # repetidas, y ordenarlos por secuencia los entrelaza en zigzag.
        tramos, ultimo = [], None
        for seq, x, y in puntos[sid]:
            if ultimo is None or seq <= ultimo:
                tramos.append([])
            tramos[-1].append((x, y))
            ultimo = seq
        tramos = [[[round(x, 5), round(y, 5)] for x, y in simplificar(t)]
                  for t in tramos if len(t) > 1]
        geom = ({"type": "LineString", "coordinates": tramos[0]} if len(tramos) == 1
                else {"type": "MultiLineString", "coordinates": tramos})
        feats.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": rid,
                "corto": corto(r),
                "nombre": largo(r),
                "agencia": agencias.get(r["agency_id"], r["agency_id"]),
                "tipo": int(r["route_type"]),
                "color": "#" + (r.get("route_color") or "666666"),
                "sentido": int(sentido),
                "destino": destino,
                "frec_min": None,  # lo llena analisis.py
                "revisar": bool(lista is not None and r["agency_id"] == "BUS" and rid not in lista),
            },
        })

    # paradas: qué rutas pasan (por route_id: hay nombres cortos repetidos,
    # p. ej. T01 en Mi Macro Periférico y en Mi Macro Aeropuerto)
    rep = {tid: rid for (rid, _, _), tid in viaje_rep.items()}
    rutas_parada = defaultdict(set)
    for st in filas(gtfs, "stop_times.txt"):
        rid = rep.get(st["trip_id"])
        if rid:
            rutas_parada[st["stop_id"]].add(rid)
    paradas = [{
        "type": "Feature",
        "geometry": {"type": "Point",
                     "coordinates": [round(float(s["stop_lon"]), 5), round(float(s["stop_lat"]), 5)]},
        "properties": {"nombre": s["stop_name"].strip(), "rutas": sorted(rutas_parada[s["stop_id"]])},
    } for s in leer(gtfs, "stops.txt") if rutas_parada.get(s["stop_id"])]

    for nombre, fs in (("rutas.geojson", feats), ("paradas.geojson", paradas)):
        with open(salida / nombre, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": fs}, f,
                      ensure_ascii=False, separators=(",", ":"))
    print(f"{len(feats)} trazos de {len({f['properties']['id'] for f in feats})} rutas, "
          f"{len(paradas)} paradas")


if __name__ == "__main__":
    main(*sys.argv[1:4])
