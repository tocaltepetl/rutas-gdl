# Rutas de camiones GDL

> **English:** an unofficial watchdog of Guadalajara's public transit data.
> Since Sept. 2026 SETRAN publishes a current GTFS feed (hosted by a private
> vendor, Ualabee), but with no explicit open license, no official portal
> listing and no public real-time data. This site shows what is still missing, helps people request the data via transparency
> laws, and proves what can be built with open data alone. Contributions
> welcome — see
> [CONTRIBUTING](https://github.com/tocaltepetl/.github/blob/main/CONTRIBUTING.md)
> (in Spanish; English is fine in issues and PRs).

**Desde el 30 de septiembre de 2026 SETRAN
[publica el GTFS vigente](https://setran.jalisco.gob.mx/prensa/notas-web/archivos-gtfs-del-transporte-publico)
de las rutas. Falta que sea dato abierto de verdad: licencia explícita,
publicación en el portal oficial con enlace estable, y tiempo real público.**

Este proyecto no oficial busca que la información de transporte público de la
zona metropolitana de Guadalajara (Mi Transporte, Mi Macro, Mi Tren, Si Tren y
Mi Transporte Eléctrico) sea de todos y no solo de las plataformas privadas:

1. **Muestra qué falta**: qué datos son abiertos, cuáles están cerrados y qué
   tan viejos son ([estado de los datos](https://rutasgdl.tocaltepetl.org/datos.html)).
2. **Te ayuda a pedirlos**: una guía para solicitar por transparencia a SETRAN
   y SITEUR la licencia, la publicación oficial y el tiempo real, más un registro público y anónimo de
   folios ([pide los datos](https://rutasgdl.tocaltepetl.org/solicitar.html)).
3. **Demuestra lo que se puede hacer con datos abiertos**: un mapa de la red
   completa y análisis de cobertura y frecuencias, hecho con el GTFS que
   publica SETRAN y OpenStreetMap.

**Para quién:** periodistas, colectivos de movilidad, academia y cualquier
persona que quiera exigir mejores datos. Para planear un viaje, Google Maps o
Mi Ruta te sirven mejor. Ver [decisiones](docs/decisiones.md#propósito-2026-11-14).

## Qué muestra
- Las rutas con su trazo y color oficial sobre OpenStreetMap.
- Búsqueda por número, nombre o destino, y filtro por sistema.
- Al elegir una ruta se resalta y se puede compartir el enlace (`#ruta=C01`).
- Al tocar el mapa: las rutas con alguna parada a menos de 300 m. El punto no
  sale del navegador.
- Frecuencia aproximada en hora pico, según el GTFS.
- [Pide los datos](https://rutasgdl.tocaltepetl.org/solicitar.html): guía para
  pedir por transparencia a SETRAN y SITEUR lo que falta (licencia, portal
  oficial, tiempo real, GTFS completo de SITEUR), y
  registro público y anónimo de folios (sin nombre ni correo; la IP no se
  guarda). Dato abierto en `/api/solicitudes.csv` y `/api/solicitudes`.

- [Estado de los datos](public/datos.html) (`/datos.html`): qué es abierto, qué
  está cerrado, qué tan viejo es y qué se ha pedido por transparencia.
- [Análisis](public/analisis.html) (`/analisis.html`): cobertura a pie (malla
  de 250 m), frecuencias por ruta y corredores con más rutas encimadas.
- [Guía de mapeo](docs/mapeo.md) para mejorar las rutas en OpenStreetMap (el
  único lugar donde son dato abierto con licencia).
- Vigilancia semanal (`.github/workflows/mdb-monitor.yml`):
  - del enlace de SETRAN (`scripts/setran_estado.py` → `public/data/setran.json`):
    fecha, tamaño, archivos internos y fin del calendario, leyendo solo ~70 KB
    del ZIP; abre un issue si falla o vence en menos de 30 días;
  - del GTFS anterior en la Mobility Database (`scripts/mdb_estado.py` →
    `public/data/mdb.json`) y de si aparece un feed nuevo de Jalisco.
  Ambos se muestran en «Estado de los datos».
- Conteo de visitas con Cloudflare Web Analytics (sin cookies ni datos
  personales). Ver la
  [política de privacidad común](https://github.com/tocaltepetl/.github/blob/main/docs/privacidad.md).

## Datos
GTFS que SETRAN Jalisco publica desde el 30-sep-2026
([nota](https://setran.jalisco.gob.mx/prensa/notas-web/archivos-gtfs-del-transporte-publico)):
`https://ualabee.com/api/v3/cities/35/gtfs-feeds/public` (redirige a un ZIP de
~52 MB alojado por Ualabee). Al 2026-11-14: 401 rutas de 11 sistemas,
calendario hasta el 2026-12-31, sin `feed_info.txt` ni licencia explícita.

- Hasta noviembre de 2026 se usó el GTFS de marzo de 2024 de
  [datos.jalisco.gob.mx](https://datos.jalisco.gob.mx/dataset/actualizacion-de-rutas-de-transporte-publico-colectivo-y-masivo-en-la-zona-metropolitana-de)
  (`gtfs_amg_20240312.zip`), copia de la
  [Mobility Database (mdb-2366)](https://mobilitydatabase.org/feeds/gtfs/mdb-2366).
  Ver [decisiones](docs/decisiones.md).

Para regenerar `public/data/`:

```sh
curl -L -o /tmp/gtfs.zip https://ualabee.com/api/v3/cities/35/gtfs-feeds/public
unzip -o /tmp/gtfs.zip -d /tmp/gtfs
python3 -I scripts/gtfs_a_geojson.py /tmp/gtfs public/data datos/lineas-treep-mi-transporte.txt
python3 -I scripts/analisis.py /tmp/gtfs public/data   # analisis.json y GeoJSON del análisis
```

### Rutas de OpenStreetMap
Las rutas que están en OSM y no en el GTFS (hoy MP-T04 y la Línea 4 del tren)
se muestran con línea discontinua y la marca «Fuente: OpenStreetMap». Son
© colaboradores de OpenStreetMap y `public/data/rutas_osm.geojson` se publica
bajo [ODbL](https://opendatacommons.org/licenses/odbl/). Para regenerarlo, y el
reporte `datos/comparacion-osm.md` (después de generar `rutas.geojson`):

```sh
python3 -I scripts/osm_rutas.py /tmp/gtfs public/data
```

### Reportar cambios
Con una ruta elegida, «Reportar un cambio en esta ruta» publica una nota
**pública y anónima** en OpenStreetMap en el punto que marques, con
`#rutasgdl` ([ver las abiertas](https://www.openstreetmap.org/api/0.6/notes/search?q=rutasgdl&closed=0)).
Para probar sin crear notas reales: `?osm=dev` (servidor de pruebas de OSM).

## Comparación con otras ciudades

`public/data/comparativa.json` (sección «Otras ciudades sí publican» de
`analisis.html`) sale del catálogo de [Mobility Database](https://mobilitydatabase.org/).
Para regenerarlo (solo biblioteca estándar; tarda menos de un minuto):

```sh
python3 -I scripts/comparativa_mdb.py
```

Lee `feeds_v2.csv`, toma los feeds GTFS y GTFS-RT de México (por estado) y de
las áreas metropolitanas de la lista `METROS` del script, y descarga en memoria
el `latest.zip` de los GTFS no *deprecated* para leer su calendario. «Vigente»
= la fecha máxima de servicio (`calendar.txt`, `calendar_dates.txt` o
`feed_info.txt`) llega al día del corte o después. La fecha del corte queda en
el campo `corte`.

## Uso local

```sh
python3 -m http.server 8765 --directory public
```

Con el Worker y la base D1 local (registro de solicitudes):

```sh
npx -y wrangler@4.160.1 d1 migrations apply DB --local
npx -y wrangler@4.160.1 dev --local
```

## Contribuir
Issues y PRs bienvenidos. Lee el
[CONTRIBUTING común](https://github.com/tocaltepetl/.github/blob/main/CONTRIBUTING.md)
y el [código de conducta](https://github.com/tocaltepetl/.github/blob/main/CODE_OF_CONDUCT.md).

## Licencia
El código: [MIT](LICENSE). Los datos de rutas son de SETRAN Jalisco (publicados
sin licencia explícita; la pedimos por transparencia); el mapa base es © colaboradores de OpenStreetMap.

## Publicación
Sitio: **https://rutasgdl.tocaltepetl.org** (Cloudflare Workers: archivos
estáticos y un Worker para `/api/*` con D1). Se publica desde GitHub Actions al liberar una versión.
