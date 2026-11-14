#!/usr/bin/env python3
"""Convierte el GTFS de la ZMG en GeoJSON ligero para el mapa.

Uso: python3 -I scripts/gtfs_a_geojson.py <carpeta_gtfs_descomprimida> public/data [datos/lineas-treep-mi-transporte.txt]

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
    rutas = {r["route_id"]: r for r in leer(gtfs, "routes.txt")}

    puntos = defaultdict(list)
    for p in leer(gtfs, "shapes.txt"):
        puntos[p["shape_id"]].append(
            (int(p["shape_pt_sequence"]), float(p["shape_pt_lon"]), float(p["shape_pt_lat"]))
        )

    # headway mínimo por viaje (frecuencia en hora pico)
    frec = {}
    for f in leer(gtfs, "frequencies.txt"):
        h = int(f["headway_secs"])
        frec[f["trip_id"]] = min(h, frec.get(f["trip_id"], h))

    # un shape por (ruta, sentido); y viajes representativos para paradas
    vistos = {}
    viaje_rep = {}
    frec_ruta = {}
    for t in leer(gtfs, "trips.txt"):
        clave = (t["route_id"], t.get("direction_id") or "0", t["shape_id"])
        vistos.setdefault(clave, t.get("trip_headsign", ""))
        viaje_rep.setdefault(clave, t["trip_id"])
        if t["trip_id"] in frec:
            r = t["route_id"]
            frec_ruta[r] = min(frec[t["trip_id"]], frec_ruta.get(r, 10**9))

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
                "corto": r["route_short_name"],
                "nombre": r["route_long_name"],
                "agencia": agencias.get(r["agency_id"], r["agency_id"]),
                "tipo": int(r["route_type"]),
                "color": "#" + (r.get("route_color") or "666666"),
                "sentido": int(sentido),
                "destino": destino,
                "frec_min": round(frec_ruta[rid] / 60) if rid in frec_ruta else None,
                "revisar": bool(lista is not None and r["agency_id"] == "BUS" and rid not in lista),
            },
        })

    # paradas: qué rutas pasan
    rep = {tid: rid for (rid, _, _), tid in viaje_rep.items()}
    rutas_parada = defaultdict(set)
    for st in leer(gtfs, "stop_times.txt"):
        rid = rep.get(st["trip_id"])
        if rid:
            rutas_parada[st["stop_id"]].add(rutas[rid]["route_short_name"])
    paradas = [{
        "type": "Feature",
        "geometry": {"type": "Point",
                     "coordinates": [round(float(s["stop_lon"]), 5), round(float(s["stop_lat"]), 5)]},
        "properties": {"nombre": s["stop_name"], "rutas": sorted(rutas_parada[s["stop_id"]])},
    } for s in leer(gtfs, "stops.txt") if rutas_parada.get(s["stop_id"])]

    for nombre, fs in (("rutas.geojson", feats), ("paradas.geojson", paradas)):
        with open(salida / nombre, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": fs}, f,
                      ensure_ascii=False, separators=(",", ":"))
    print(f"{len(feats)} trazos de {len({f['properties']['id'] for f in feats})} rutas, "
          f"{len(paradas)} paradas")


if __name__ == "__main__":
    main(*sys.argv[1:4])
