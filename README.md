# Rutas de camiones GDL

> **English:** an unofficial watchdog of Guadalajara's public transit data.
> SETRAN gave Google the 2026 routes but only publishes 2024 data as open data.
> This site shows the gap, helps people request the data via transparency
> laws, and proves what can be built with open data alone. Contributions
> welcome — see
> [CONTRIBUTING](https://github.com/tocaltepetl/.github/blob/main/CONTRIBUTING.md)
> (in Spanish; English is fine in issues and PRs).

**SETRAN entregó a Google Maps las rutas de 2026, pero como datos abiertos solo
publica las de marzo de 2024. Y el tiempo real no se publica.**

Este proyecto no oficial busca que la información de transporte público de la
zona metropolitana de Guadalajara (Mi Transporte, Mi Macro, Mi Tren, Si Tren y
Mi Transporte Eléctrico) sea de todos y no solo de las plataformas privadas:

1. **Muestra qué falta**: qué datos son abiertos, cuáles están cerrados y qué
   tan viejos son ([estado de los datos](https://rutasgdl.tocaltepetl.org/datos.html)).
2. **Te ayuda a pedirlos**: una guía para solicitar por transparencia a SETRAN
   y SITEUR el GTFS y el tiempo real, más un registro público y anónimo de
   folios ([pide los datos](https://rutasgdl.tocaltepetl.org/solicitar.html)).
3. **Demuestra lo que se puede hacer con datos abiertos**: un mapa de la red
   completa y análisis de cobertura y frecuencias, todo hecho solo con el GTFS
   oficial y OpenStreetMap.

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
  pedir por transparencia a SETRAN y SITEUR sus datos (GTFS y tiempo real), y
  registro público y anónimo de folios (sin nombre ni correo; la IP no se
  guarda). Dato abierto en `/api/solicitudes.csv` y `/api/solicitudes`.

- [Estado de los datos](public/datos.html) (`/datos.html`): qué es abierto, qué
  está cerrado, qué tan viejo es y qué se ha pedido por transparencia.
- [Análisis](public/analisis.html) (`/analisis.html`): cobertura a pie (malla
  de 250 m), frecuencias por ruta y corredores con más rutas encimadas.
- [Guía de mapeo](docs/mapeo.md) para completar en OpenStreetMap las 58 rutas
  que faltan en los datos abiertos.
- Conteo de visitas con Cloudflare Web Analytics (sin cookies ni datos
  personales). Ver la
  [política de privacidad común](https://github.com/tocaltepetl/.github/blob/main/docs/privacidad.md).

## Datos
GTFS de SETRAN Jalisco publicado en
[datos.jalisco.gob.mx](https://datos.jalisco.gob.mx/dataset/actualizacion-de-rutas-de-transporte-publico-colectivo-y-masivo-en-la-zona-metropolitana-de)
(`gtfs_amg_20240312.zip`, marzo de 2024). Como el portal no respondía, se tomó
la copia de la [Mobility Database (mdb-2366)](https://mobilitydatabase.org/feeds/gtfs/mdb-2366).

- 275 rutas en el GTFS; 247 tienen trazo y son las que aparecen en el mapa.
- Son datos de 2024: algunas rutas pudieron cambiar. SETRAN tiene una versión
  de 2026 en Google Maps que no ha publicado como datos abiertos.

Para regenerar `public/data/`:

```sh
curl -L -o /tmp/gtfs.zip https://files.mobilitydatabase.org/mdb-2366/latest.zip
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
El código: [MIT](LICENSE). Los datos de rutas son de SETRAN Jalisco (licencia
por confirmar en su portal); el mapa base es © colaboradores de OpenStreetMap.

## Publicación
Sitio: **https://rutasgdl.tocaltepetl.org** (Cloudflare Workers: archivos
estáticos y un Worker para `/api/*` con D1). Se publica desde GitHub Actions al liberar una versión.
