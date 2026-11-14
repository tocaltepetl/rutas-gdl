# Rutas de camiones GDL

> **English:** free, ad-free map of public transit routes in the Guadalajara
> metropolitan area, built from the Jalisco government's open GTFS data. A
> static page, no backend, no accounts. Contributions welcome — see
> [CONTRIBUTING](https://github.com/tocaltepetl/.github/blob/main/CONTRIBUTING.md)
> (in Spanish; English is fine in issues and PRs).

Observatorio **no oficial** de las rutas de transporte público de la zona
metropolitana de Guadalajara (Mi Transporte, Mi Macro, Mi Tren, Si Tren y Mi
Transporte Eléctrico): un mapa libre y sin anuncios, el estado de los datos
abiertos y análisis de la red.

La información pública de transporte debería llegar a la ciudadanía sin
depender de plataformas privadas. Este proyecto usa solo datos abiertos (GTFS
oficial y OpenStreetMap) y busca que SETRAN y SITEUR publiquen los suyos,
incluido el tiempo real. Ver [decisiones](docs/decisiones.md#propósito-2026-11-14).

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
