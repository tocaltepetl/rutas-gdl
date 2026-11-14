# Decisiones

## Propósito (2026-11-14)
Un **observatorio de las rutas de transporte público** de la ZMG, no otra app
para planear viajes: Google Maps y Mi Ruta (SITEUR) ya lo hacen mejor. Lo que
aporta el proyecto:
1. Ver la red completa: trazos, qué rutas pasan por un punto, enlaces por ruta.
2. Apertura de datos: solicitudes de transparencia, y mostrar qué es abierto,
   qué tan viejo está y qué se ha pedido.
3. Análisis con datos abiertos: cobertura, frecuencias y, con tiempo real,
   cumplimiento del servicio.
4. Datos limpios y reutilizables para otros proyectos.

**Principio:** la información pública de transporte debe llegar a la
ciudadanía sin pasar por plataformas privadas. Por eso: solo fuentes abiertas
(GTFS oficial, OpenStreetMap); nada de Google ni de APIs privadas o protegidas;
mapa base de OpenStreetMap; y la meta es que SETRAN y SITEUR publiquen sus
datos (GTFS y GTFS-Realtime) como datos abiertos para cualquiera.

## 2026-11-14 — prototipo

### Fuente de datos
**Opciones revisadas:** Moovit (freemium con anuncios, datos cerrados) · Google
Maps (SETRAN cargó 275 rutas en 2026, pero el GTFS no es público) · Ualabee
(tiempo real, app propia y cerrada) · GTFS de datos.jalisco.gob.mx.
**Elegida:** el GTFS de datos.jalisco.gob.mx (`gtfs_amg_20240312.zip`), el único
abierto. El 2026-11-14 el dominio del portal no resolvía, así que se usó la
copia de la Mobility Database (`files.mobilitydatabase.org/mdb-2366/latest.zip`).

**Pendiente:** confirmar la licencia en el portal y pedir a SETRAN, por
transparencia, el GTFS actual que entregó a Google.

### Conversión a GeoJSON previa, no GTFS en el navegador
`scripts/gtfs_a_geojson.py` (solo biblioteca estándar) genera `rutas.geojson`
(un trazo por ruta y sentido, simplificado a ~3 m) y `paradas.geojson`. La
página solo carga dos archivos estáticos (~1 MB y ~1.5 MB sin comprimir).

### Error en el GTFS: T14B_r1
Trae dos tramos con `shape_pt_sequence` repetidas; ordenar por secuencia los
entrelaza en zigzag. El script respeta el orden del archivo y parte el trazo
donde la secuencia reinicia (`MultiLineString`).

### Mapa
Leaflet 1.9.4 (cdnjs) con teselas de OpenStreetMap y render en canvas. Al tocar
el mapa se buscan paradas a menos de 300 m en el navegador; el punto no se
envía a ningún lado.

### Despliegue
Igual que camiones-basura-gdl: Cloudflare Workers con assets estáticos,
dominio `rutasgdl.tocaltepetl.org`, versión por títulos de PR (Conventional
Commits) y aprobación en el ambiente «production».

### Conteo de visitas
Cloudflare Web Analytics, beacon a mano antes de `</body>` (los Workers con
custom domain no lo inyectan). Sin cookies ni datos personales; se avisa en el
pie de la página con enlace a la política de privacidad común.

## 2026-11-14 — rutas que pudieron cambiar

treep.app (de la misma empresa que Ualabee, según sus enlaces a tiendas)
lista 275 líneas de Mi Transporte con los identificadores del GTFS de SETRAN,
pero de una versión más nueva: 21 líneas del GTFS 2024 ya no aparecen (casi
todas se dividieron en variantes) y hay 58 identificadores nuevos.

**Decisión:** no copiar sus trazos ni paradas (datos de un privado sin
licencia). Solo se guarda la lista de identificadores en
`datos/lineas-treep-mi-transporte.txt` y el script marca con `revisar` las
líneas de Mi Transporte que no están en ella; la página muestra un aviso.
De las 21, solo 5 tienen trazo en el mapa (C05, C104, C117, C138, T09-O).
Las nuevas no se pueden mostrar hasta tener el GTFS actual.

## 2026-11-14 — Registro de solicitudes
`public/solicitar.html` guía a la ciudadanía para enviar en la PNT las dos
solicitudes de `docs/solicitudes-transparencia.md` (solo el «Texto para
pegar», con botón de copiar) y trae una plantilla de recurso de revisión sin
plazos inventados («revisa el plazo en la PNT»). La página no envía nada por
la persona.

Tras enviarla, la persona puede registrar **sujeto obligado, folio y fecha**,
y después el estado de la respuesta. Un Worker mínimo (`src/worker.js`, solo
`/api/*` vía `run_worker_first`) con D1 (`rutas-gdl`, `migrations/`):
- `POST /api/solicitudes`: folio de 10 a 20 números, fecha entre 2026-11-01 y
  hoy (hora de Guadalajara); un folio solo se registra una vez (409).
- `POST`/`PATCH /api/solicitudes/:folio/estado`: sin respuesta, entregada,
  entregada parcial, negada o prórroga, con fecha (entre el envío y hoy).
- `GET /api/solicitudes` (totales por sujeto y estado, mediana y máximo de
  días sin respuesta, lista de folios) y `GET /api/solicitudes.csv`, ambos con
  CORS abierto como datos abiertos.

**Privacidad:** no se piden nombre, correo ni texto libre; los folios ya son
públicos en la PNT y nunca se ligan con quien los registró. Contra spam, un
límite de 10 escrituras por minuto por IP con Workers Rate Limiting (binding
`LIMITE`): la IP solo se usa en memoria y no se guarda, como pide la
[política común](https://github.com/tocaltepetl/.github/blob/main/docs/privacidad.md).
(Una primera versión guardaba un hash diario de la IP en D1; se quitó por
contradecir esa política.)

**Límites conocidos:** cualquiera que conozca un folio puede cambiar su
estado (no hay cuentas, a propósito); los datos los captura la ciudadanía y
hay que verificarlos en la PNT. **Pendiente:** crear la base
(`wrangler d1 create rutas-gdl`) y poner su id en `wrangler.jsonc`. Las migraciones se aplican en
`release.yml` antes de desplegar.

## 2026-11-14 — estado de los datos, análisis y mapeo

### Página «Estado de los datos» (`public/datos.html`)
Tabla de fuentes (GTFS 2024, GTFS 2026, tiempo real SETRAN/Ualabee y SITEUR,
OpenStreetMap, IMEPLAN) con «¿abierto?», «¿al día?» y fecha de consulta, más
las solicitudes de transparencia. Página estática sin JS propio.

### Análisis (`scripts/analisis.py` → `public/analisis.html`)
Solo biblioteca estándar; lee los GeoJSON ya generados y `frequencies.txt`.
- **Cobertura:** malla de 250 m en proyección local equirectangular. Área de
  estudio = celdas a ≤ 2 km de alguna parada (recorte del área urbana sin
  depender de un polígono externo); se publica también la cifra con 1 km
  para mostrar cuánto depende del recorte. «Sin cobertura a pie» = parada más
  cercana a > 500 m en línea recta. Resultado (GTFS 2024): 49.8 % de las
  celdas con el recorte de 2 km, 31.1 % con el de 1 km.
  **Limitación:** es área, no población. Fuente abierta propuesta: INEGI,
  Censo 2020, «Principales resultados por AGEB y manzana urbana» (descarga sin
  registro, por estado: Jalisco, CSV y cartografía del Marco Geoestadístico;
  del orden de decenas de MB comprimido; verificar tamaño y licencia antes de
  descargar). No se descargó.
- **Frecuencias:** solo servicio que corre en lunes. Pico = ventana activa a
  las 08:00 (la menor entre sentidos). Nocturno = salidas después de las 23:00
  o antes de las 05:00. Son horarios programados; el cumplimiento requiere
  tiempo real.
- **Corredores:** trazos de `rutas.geojson` muestreados cada 20 m sobre una
  malla de 150 m; rutas distintas por celda (los dos sentidos cuentan una).
  Los pares viales de un sentido reparten las rutas y quedan subcontados.
- La página no carga `sin_cobertura.geojson` (1.1 MB, puntos): dibuja la malla
  compacta de `analisis.json` (~380 KB) en canvas. Los GeoJSON quedan para
  reutilizarlos.

### Guía de mapeo (`docs/mapeo.md`)
OpenStreetMap es la única vía abierta para las 58 rutas que no están en el
GTFS 2024. La guía da solo identificadores; prohíbe copiar trazos de Treep,
Google o Moovit. Coordinación con issues etiquetados `mapeo`.

## 2026-11-14 — reportes y rutas de OpenStreetMap

### «Reportar un cambio en esta ruta» con notas de OSM
**Opciones:** formulario propio con backend (requiere guardar datos y moderar),
issues de GitHub (requiere cuenta), notas de OpenStreetMap.
**Elegida:** notas de OSM (`POST /api/0.6/notes.json`): anónimas, sin cuenta,
públicas, y quien mapea en OSM las ve y puede corregir el mapa. La persona
marca el punto y elige un motivo; antes de enviar se muestra que será una nota
PÚBLICA y anónima, con el texto exacto (ruta, sistema, motivo y
`#rutasgdl`). Solo se envían ese punto y ese texto, nunca la ubicación del
dispositivo. Opcionalmente se muestran las notas abiertas con `#rutasgdl` de
la zona visible (desactivado por defecto: no se consulta a OSM sin que la
persona lo pida). `?osm=dev` usa `master.apis.dev.openstreetmap.org` para
probar sin crear notas reales. La API de OSM responde con CORS abierto; no hay
CSP en el sitio (si se agrega: `connect-src api.openstreetmap.org
master.apis.dev.openstreetmap.org`).

### Rutas de OpenStreetMap que faltan en el GTFS
`scripts/osm_rutas.py` consulta Overpass y agrega a `public/data/rutas_osm.geojson`
solo las rutas cuyo `ref` no está en el GTFS (por `route_id`, por clave corta
única, y `TL-n`/`ST-Ln` de OSM ↔ `MT_Ln`/`ST_Ln` del GTFS), y las del GTFS sin
trazo que sí lo tengan en OSM. Se marcan «Fuente: OpenStreetMap
(colaborativo)» con línea discontinua. Resultado del 2026-11-14: solo 2 rutas
(MP-T04 y la Línea 4 del tren); casi todas las relaciones de la zona,
importadas en 2022, tienen paradas pero no las calles del recorrido. Detalle en
`datos/comparacion-osm.md`.

**Licencia:** los datos de OSM son © colaboradores de OpenStreetMap bajo ODbL;
`rutas_osm.geojson` es una base de datos derivada y se publica bajo ODbL
(atribución visible en el mapa y en el pie). El GTFS no se mezcla en el mismo
archivo.

## 2026-11-14 — ajustes para cumplir la política de privacidad común
- Registro de solicitudes: el límite contra spam ya no guarda un hash de la IP
  en D1; usa Workers Rate Limiting en memoria (ver «Registro de solicitudes»).
  Se quitó la tabla `limites` y el secreto `SAL`.
- Reporte de cambios en OSM: se quitó el comentario libre; solo ruta, motivo
  (lista cerrada) y punto. Quien quiera dar detalle puede comentar la nota en
  OpenStreetMap con su propia cuenta.

## 2026-11-14 — identidad visual
- Familia de tocaltepetl (como camiones-basura-gdl y estado-gob): cerro en
  contorno con agua y, dentro del arco, el glifo del proyecto: **una ruta en
  zigzag (terracota) con cuatro paradas (verde)**.
- Colores: tinta `#1D2420`, papel `#EFE9DC`, agua `#3F86A8`, verde `#2F6B4F`,
  terracota `#B5532C`. Las páginas usan esa paleta (acento agua `#2C6E8E` en
  claro, `#6FB3D2` en oscuro). Wordmark «rutas gdl» en Bricolage Grotesque 700
  (OFL), convertido a trazos: no depende de la fuente.
- `assets/brand/` es la fuente y no se publica (incluye copia de los logos de
  tocaltepetl y `og-fuente.svg`); se generan con `scripts/marca.py` (necesita
  fontTools en un venv y el TTF de Bricolage). A `public/` solo van
  `favicon.svg` (sin scripts ni referencias externas; se adapta a modo oscuro)
  y `og.png` (1200×630). Open Graph/Twitter apuntan a `https://rutasgdl.tocaltepetl.org/`.
