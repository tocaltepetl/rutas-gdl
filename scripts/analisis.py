#!/usr/bin/env python3
"""Análisis de la red con datos abiertos (GTFS SETRAN 2024). Solo biblioteca estándar.

Uso: python3 -I scripts/analisis.py <carpeta_gtfs_descomprimida> public/data

Lee `paradas.geojson` y `rutas.geojson` (generados por gtfs_a_geojson.py) y
`trips.txt`, `frequencies.txt` y `routes.txt` del GTFS. Genera en public/data:

  analisis.json           resumen, tabla de frecuencias por ruta, malla de
                          cobertura compacta y corredores
  sin_cobertura.geojson   centros de las celdas de 250 m a más de 500 m de toda parada
  corredores.geojson      celdas de 150 m por donde pasan más rutas

Métodos (ver docs/decisiones.md):
  - Cobertura: malla de 250 m en una proyección local equirectangular
    (error < 0.5 % en la ZMG). Área de estudio: celdas cuyo centro está a
    <= 2 km de alguna parada (recorte del área urbana; ver ESTUDIO_M).
    Por celda: distancia a la parada más cercana y número de rutas distintas
    con alguna parada a <= 500 m.
  - Frecuencias: solo servicio entre semana (service_id con lunes = 1). Por
    ruta: primera salida, última salida, intervalo mínimo y máximo, intervalo
    en hora pico (ventana activa a las 08:00; si hay varias, la menor) y si
    hay salidas después de las 23:00 o antes de las 05:00 (servicio nocturno).
  - Corredores: los trazos se muestrean cada 20 m sobre una malla de 150 m;
    por celda se cuentan rutas distintas (ambos sentidos cuentan una vez).
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict

LAT0 = 20.67
KX = 111320 * math.cos(math.radians(LAT0))  # m por grado de longitud
KY = 110574                                 # m por grado de latitud
CELDA = 250       # m, malla de cobertura
A_PIE = 500       # m, distancia caminable a una parada
ESTUDIO_M = 2000  # m, recorte del área de estudio
CELDA_COR = 150   # m, malla de corredores
PASO = 20         # m, muestreo de trazos
PICO = 8 * 3600   # 08:00
NOCHE_INI, NOCHE_FIN = 23 * 3600, 5 * 3600


def xy(lon, lat):
    return lon * KX, lat * KY


def lonlat(x, y):
    return x / KX, y / KY


def seg(t):
    h, m, s = (int(v) for v in t.split(':'))
    return h * 3600 + m * 60 + s


def hhmm(s):
    return f'{s // 3600:02d}:{s % 3600 // 60:02d}'


def cobertura(paradas):
    pts = []
    for f in paradas['features']:
        x, y = xy(*f['geometry']['coordinates'])
        pts.append((x, y, set(f['properties'].get('rutas', []))))
    # índice espacial por cubetas de 500 m
    cub = defaultdict(list)
    for p in pts:
        cub[(int(p[0] // A_PIE), int(p[1] // A_PIE))].append(p)
    x0 = min(p[0] for p in pts) - ESTUDIO_M
    y0 = min(p[1] for p in pts) - ESTUDIO_M
    nx = int((max(p[0] for p in pts) + ESTUDIO_M - x0) // CELDA) + 1
    ny = int((max(p[1] for p in pts) + ESTUDIO_M - y0) // CELDA) + 1
    anillos = math.ceil(ESTUDIO_M / A_PIE)
    celdas = []
    for j in range(ny):
        cy = y0 + (j + 0.5) * CELDA
        for i in range(nx):
            cx = x0 + (i + 0.5) * CELDA
            bx, by = int(cx // A_PIE), int(cy // A_PIE)
            dmin = None
            rutas = set()
            for dx in range(-anillos, anillos + 1):
                for dy in range(-anillos, anillos + 1):
                    for px, py, rs in cub.get((bx + dx, by + dy), ()):
                        d = math.hypot(px - cx, py - cy)
                        if dmin is None or d < dmin:
                            dmin = d
                        if d <= A_PIE:
                            rutas |= rs
            if dmin is not None and dmin <= ESTUDIO_M:
                celdas.append((i, j, round(dmin), len(rutas)))
    return x0, y0, celdas


def caja(x0, y0, i, j, lado):
    a = lonlat(x0 + i * lado, y0 + j * lado)
    b = lonlat(x0 + (i + 1) * lado, y0 + (j + 1) * lado)
    r = lambda v: round(v, 5)
    return [[[r(a[0]), r(a[1])], [r(b[0]), r(a[1])], [r(b[0]), r(b[1])],
             [r(a[0]), r(b[1])], [r(a[0]), r(a[1])]]]


def frecuencias(gtfs, info):
    abrir = lambda n: csv.DictReader(open(os.path.join(gtfs, n), encoding='utf-8-sig'))
    lunes = {r['service_id'] for r in abrir('calendar.txt') if r['monday'] == '1'}
    viaje = {r['trip_id']: r['route_id'] for r in abrir('trips.txt') if r['service_id'] in lunes}
    nombres = {r['route_id']: r for r in abrir('routes.txt')}
    ventanas = defaultdict(list)
    for r in abrir('frequencies.txt'):
        ruta = viaje.get(r['trip_id'])
        if ruta:
            ventanas[ruta].append((seg(r['start_time']), seg(r['end_time']), int(r['headway_secs'])))
    filas = []
    for ruta, vs in sorted(ventanas.items()):
        n = nombres.get(ruta, {})
        pico = [h for a, b, h in vs if a <= PICO < b]
        ini = min(a for a, _, _ in vs)
        fin = max(b for _, b, _ in vs)
        nocturno = any(b > NOCHE_INI or a < NOCHE_FIN for a, b, _ in vs)
        filas.append({
            'id': ruta,
            'corto': n.get('route_short_name') or ruta,
            'nombre': n.get('route_long_name', ''),
            'agencia': info.get(ruta, {}).get('agencia', ''),
            'trazo': ruta in info,
            'revisar': info.get(ruta, {}).get('revisar', False),
            'primera': hhmm(ini),
            'ultima': hhmm(fin),
            'min_min': round(min(h for *_, h in vs) / 60),
            'max_min': round(max(h for *_, h in vs) / 60),
            'pico_min': round(min(pico) / 60) if pico else None,
            'nocturno': nocturno,
        })
    return filas


def corredores(rutas):
    celdas = defaultdict(set)
    for f in rutas['features']:
        rid = f['properties']['id']
        g = f['geometry']
        lineas = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for linea in lineas:
            pts = [xy(*c) for c in linea]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                n = max(1, int(math.hypot(bx - ax, by - ay) // PASO))
                for k in range(n + 1):
                    t = k / n
                    x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                    celdas[(int(x // CELDA_COR), int(y // CELDA_COR))].add(rid)
    return celdas


def main(gtfs, salida):
    leer = lambda n: json.load(open(os.path.join(salida, n), encoding='utf-8'))
    paradas, rutas = leer('paradas.geojson'), leer('rutas.geojson')
    info = {f['properties']['id']: f['properties'] for f in rutas['features']}
    nombre_parada = [(xy(*f['geometry']['coordinates']), f['properties']['nombre'])
                     for f in paradas['features']]

    # a) cobertura
    x0, y0, celdas = cobertura(paradas)
    sin = [c for c in celdas if c[2] > A_PIE]
    una = [c for c in celdas if c[2] <= A_PIE and c[3] <= 1]
    # misma cifra con un recorte más estricto (<= 1 km), para mostrar cuánto depende del recorte
    est1 = [c for c in celdas if c[2] <= 1000]
    sin1 = [c for c in est1 if c[2] > A_PIE]
    # puntos (centro de celda) en vez de polígonos: ~5 veces más ligero
    def centro(i, j):
        lon, lat = lonlat(x0 + (i + 0.5) * CELDA, y0 + (j + 0.5) * CELDA)
        return [round(lon, 4), round(lat, 4)]
    geo_sin = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'d': d},
         'geometry': {'type': 'Point', 'coordinates': centro(i, j)}}
        for i, j, d, _ in sin]}

    # b) frecuencias
    frec = frecuencias(gtfs, info)
    con_pico = [f for f in frec if f['pico_min'] is not None]

    # c) corredores
    cor = corredores(rutas)
    umbral = 15
    top = sorted(((len(v), k, v) for k, v in cor.items() if len(v) >= umbral), reverse=True)

    def cercana(cx, cy):
        return min(nombre_parada, key=lambda p: (p[0][0] - cx) ** 2 + (p[0][1] - cy) ** 2)[1]

    geo_cor = {'type': 'FeatureCollection', 'features': []}
    lista_cor = []
    for n, (i, j), v in top:
        cx, cy = (i + 0.5) * CELDA_COR, (j + 0.5) * CELDA_COR
        props = {'rutas': n, 'ids': sorted(v), 'cerca_de': cercana(cx, cy)}
        geo_cor['features'].append({'type': 'Feature', 'properties': props,
                                    'geometry': {'type': 'Polygon',
                                                 'coordinates': caja(0, 0, i, j, CELDA_COR)}})
    # top 15 lugares separados al menos 800 m entre sí
    vistos = []
    for f in geo_cor['features']:
        p = f['properties']
        c = f['geometry']['coordinates'][0]
        cx, cy = xy((c[0][0] + c[2][0]) / 2, (c[0][1] + c[2][1]) / 2)
        if any(math.hypot(cx - vx, cy - vy) < 800 for vx, vy in vistos):
            continue
        vistos.append((cx, cy))
        lista_cor.append({'cerca_de': p['cerca_de'], 'rutas': p['rutas'],
                          'lat': round((c[0][1] + c[2][1]) / 2, 5),
                          'lon': round((c[0][0] + c[2][0]) / 2, 5)})
        if len(lista_cor) == 15:
            break

    pct = lambda a, b: round(100 * len(a) / len(b), 1) if b else 0
    resumen = {
        'fuente': 'GTFS SETRAN Jalisco gtfs_amg_20240312 (copia Mobility Database mdb-2366)',
        'cobertura': {
            'celda_m': CELDA, 'a_pie_m': A_PIE, 'estudio_m': ESTUDIO_M,
            'celdas': len(celdas), 'sin_cobertura': len(sin), 'pct_sin_cobertura': pct(sin, celdas),
            'con_0_o_1_ruta': len(una), 'pct_0_o_1_ruta': pct(una, celdas),
            'celdas_1km': len(est1), 'pct_sin_cobertura_1km': pct(sin1, est1),
            'km2_sin_cobertura': round(len(sin) * CELDA * CELDA / 1e6, 1),
        },
        'frecuencias': {
            'rutas': len(frec),
            'con_dato_pico': len(con_pico),
            'pico_20_o_mas': sum(f['pico_min'] >= 20 for f in con_pico),
            'pico_30_o_mas': sum(f['pico_min'] >= 30 for f in con_pico),
            'sin_nocturno': sum(not f['nocturno'] for f in frec),
            'terminan_antes_22': sum(seg(f['ultima'] + ':00') <= 22 * 3600 for f in frec),
            'nota': 'Servicio entre semana. Pico = ventana activa a las 08:00.',
        },
        'corredores': {'celda_m': CELDA_COR, 'umbral_rutas': umbral,
                       'max_rutas': top[0][0] if top else 0, 'celdas': len(top)},
    }
    out = {
        'generado': 'scripts/analisis.py',
        'resumen': resumen,
        'frecuencias': frec,
        'corredores': lista_cor,
        # malla compacta: origen en metros de la proyección local; [i, j, dist_m, rutas]
        'malla': {'kx': KX, 'ky': KY, 'x0': x0, 'y0': y0, 'lado': CELDA,
                  'celdas': [list(c) for c in celdas]},
    }
    escribir = lambda n, d: json.dump(d, open(os.path.join(salida, n), 'w', encoding='utf-8'),
                                      ensure_ascii=False, separators=(',', ':'))
    escribir('analisis.json', out)
    escribir('sin_cobertura.geojson', geo_sin)
    escribir('corredores.geojson', geo_cor)
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
