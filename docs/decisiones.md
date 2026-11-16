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
(GTFS oficial, OpenStreetMap); nada de Google ni de APIs privadas o protegidas
(el GTFS de SETRAN alojado por Ualabee se acepta porque es el enlace que la
propia Secretaría anunció como público; ver la entrada «Cambio de fuente»);
mapa base de OpenStreetMap; y la meta es que SETRAN y SITEUR publiquen sus
datos (GTFS y GTFS-Realtime) como datos abiertos para cualquiera.

## 2026-11-14 — prototipo

### Fuente de datos
**Opciones revisadas:** Moovit (freemium con anuncios, datos cerrados) · Google
Maps (SETRAN cargó 275 rutas en 2026, pero el GTFS no es público) · Ualabee
(tiempo real, app propia y cerrada) · GTFS de datos.jalisco.gob.mx.
**Superado el 2026-11-14 (ver «Cambio de fuente»):** el GTFS 2026 sí es
público desde el 30-sep-2026.
**Elegida:** el GTFS de datos.jalisco.gob.mx (`gtfs_amg_20240312.zip`), el único
abierto. El 2026-11-14 el dominio del portal no resolvió desde nuestra red
(no verificado desde otro lado), así que se usó la
copia de la Mobility Database (`files.mobilitydatabase.org/mdb-2366/latest.zip`).

**Pendiente:** confirmar la licencia en el portal y pedir a SETRAN, por
transparencia, el GTFS actual que entregó a Google. *(Superado: SETRAN lo
publica; ahora se pide la licencia y su publicación oficial.)*

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
*Superado por «Cambio de fuente»: con el GTFS vigente de SETRAN ya no hace
falta comparar contra treep.app. La lista queda como registro histórico y
`datos.html` ya no muestra esa sección.*


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
hay que verificarlos en la PNT. La base `rutas-gdl` se creó el 2026-11-14
(`wrangler d1 create rutas-gdl`; id en `wrangler.jsonc`). Las migraciones se
aplican en `release.yml` antes de desplegar.

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
  cercana a > 500 m en línea recta. Resultado con el GTFS 2024: 49.8 % de las
  celdas con el recorte de 2 km, 31.1 % con el de 1 km. Con el feed de SETRAN
  2026 (332 rutas del AMG, 13,027 paradas, área de estudio 768 km²): 49.6 % y
  30.6 %.
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
*Actualizado con «Cambio de fuente»: las 58 rutas ya vienen en el GTFS
vigente; la guía queda para mejorar OSM, no para cubrir huecos del mapa.*
OpenStreetMap era la única vía abierta para las 58 rutas que no estaban en el
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

## 2026-11-14 — vigilancia de la Mobility Database
- *(Hasta el cambio de fuente)* el GTFS que usábamos era la copia de la
  Mobility Database (`mdb-2366`) porque el portal de datos.jalisco.gob.mx no
  respondió en nuestras consultas (`portal_responde` es lo que ve el
  runner; no prueba que esté caído para todos). Ese feed está `inactive` y
  su calendario venció el 2024-12-31.
- `scripts/mdb_estado.py` (stdlib, `python3 -I`) genera
  `public/data/mdb.json`: estado en el catálogo público `feeds_v2.csv`,
  vigencia del calendario (min/max de `calendar.txt` y `calendar_dates.txt`
  de `latest.zip`), días desde que venció, fecha/MD5/generación del zip
  (cabeceras de Google Cloud Storage), URL de origen y si responde, y los
  feeds de Jalisco/Guadalajara del catálogo.
- `datos.html` lo lee y muestra los días desde el vencimiento calculados en
  el navegador; sin JS queda un texto fijo equivalente.
- `.github/workflows/mdb-monitor.yml` corre cada lunes: si el JSON cambia
  (ignorando `revisado` y `dias_desde_vencimiento`, para no abrir un PR por
  semana) abre un PR `fix:` desde `auto/mdb-estado`; si aparece un feed nuevo
  (id distinto a 1925, 1926, 2034, 2366) o cambia la generación del zip, abre
  un issue (busca uno abierto con el mismo título antes). Solo `GITHUB_TOKEN`.
- **Sin token no hay reporte del validador:** la API de la MDB pide refresh
  token y `files.mobilitydatabase.org` solo deja leer archivos conocidos
  (`feeds_v2.csv`, `latest.zip`); el JSON lleva `validador: null`.
- Requiere activar en el repo *Settings → Actions → General → «Allow GitHub
  Actions to create and approve pull requests»*; sin eso falla `gh pr create`.
- Los PR abiertos con `GITHUB_TOKEN` no disparan otros workflows (p. ej.
  `pr-titulo`, la revisión del título): hay que cerrarlo y reabrirlo, o hacer
  un push, para que corran.
- Desde el 2026-11-14 el mismo workflow vigila también el enlace de SETRAN
  (ver «Cambio de fuente»).

### Comparación con otras ciudades (Mobility Database)
Para mostrar que publicar GTFS vigente es posible y común, comparamos Guadalajara con otras áreas metropolitanas de Latinoamérica (lista `METROS` en `scripts/comparativa_mdb.py`) y con los demás estados de México, usando el catálogo público de Mobility Database (`feeds_v2.csv`). No usamos el campo `status` del catálogo como prueba de vigencia porque no siempre coincide con el calendario del feed. Llamamos «vigente» a un GTFS que no está *deprecated* y cuyo `latest.zip` tiene servicio (calendar, calendar_dates o feed_info) hasta la fecha del corte o después. El resultado se guarda en `public/data/comparativa.json`, con la fecha del corte, y se muestra en `analisis.html`. Se regenera a mano con `python3 -I scripts/comparativa_mdb.py`. Corte inicial (2026-11-14): 9 de 20 áreas con GTFS vigente (8 en el catálogo más Guadalajara con el feed de SETRAN, que está fuera del catálogo), ninguna con GTFS-RT en el catálogo, Guadalajara sin GTFS vigente *en el catálogo* desde 2024-12-31.

*Actualización (2026-11-14):* Guadalajara sí tiene GTFS vigente desde el 30-sep-2026, pero fuera de la Mobility Database (enlace de SETRAN vía Ualabee). La comparación mide lo que está registrado en el catálogo, y la página lo aclara. El dato que sigue en pie y pesa más: `feeds_v2.csv` tiene 1,080 feeds GTFS-RT en el mundo y ninguno de MX, BR, CL, CO, AR ni PE; 0 de las 20 áreas tienen tiempo real.

## 2026-11-14 — Cambio de fuente: GTFS de SETRAN publicado vía Ualabee
**Hallazgo:** el 30-sep-2026 SETRAN anunció
([nota](https://setran.jalisco.gob.mx/prensa/notas-web/archivos-gtfs-del-transporte-publico))
que publica su GTFS en `https://ualabee.com/api/v3/cities/35/gtfs-feeds/public`.
Ese enlace redirige (302) a `platform.ualabee.com/.../latest/download` y de ahí
a Firebase Storage, ambos con token en la URL. Revisión del 2026-11-14: ZIP de
52.7 MB con archivos fechados el 2026-11-13 (se regenera seguido), calendario
2026-05-01 a 2026-12-31, 401 rutas de 11 agencias (Mi Transporte 275, Mi Macro
32, Mi Macro Periférico 5, Mi Macro Aeropuerto 4, Mi Tren 4, SiTren 11, Tepabus
19, Mi Transporte Eléctrico 1, más Puerto Vallarta y Lagos de Moreno). Las 275
líneas de Mi Transporte coinciden con las de treep.app.

Esto contradecía lo que decía el proyecto («el GTFS 2026 no es público»,
«Guadalajara sin GTFS vigente desde 2024»). Se corrigieron README,
`datos.html`, `analisis.html`, `solicitar.html` y las solicitudes.

**Decisión:** el mapa y el análisis usan este feed en lugar de
`gtfs_amg_20240312.zip` (mdb-2366). Es el enlace que la propia Secretaría
anunció como público, así que no contradice el principio de solo fuentes
abiertas, aunque no es dato abierto pleno.

**Lo que sigue faltando** (y es ahora el foco de la apertura):
- licencia abierta explícita (no hay ninguna en la nota ni en el ZIP);
- publicación en datos.jalisco.gob.mx y registro en la Mobility Database
  (verificado en `feeds_v2.csv` el 2026-11-14: no está);
- enlace estable bajo dominio del gobierno y metadatos (`feed_info.txt` no
  existe);
- GTFS-Realtime público (no hay);
- SITEUR completo (alimentadoras, tiempo real de «Mi Ruta»);
- independencia del proveedor privado que aloja el archivo.

**Riesgos:** sin licencia, el reúso tiene base débil (atribuimos a SETRAN y
enlazamos su nota); el enlace depende de Ualabee y podría cambiar; el
calendario termina el 2026-12-31.

**Vigilancia:** `scripts/setran_estado.py` (stdlib) sigue los redirects y,
con peticiones HTTP Range, lee solo el directorio central del ZIP y
`calendar*.txt` (~70 KB en vez de 52 MB; si no hay Range, descarga todo).
Escribe `public/data/setran.json`: host final, fecha/MD5/generación/tamaño,
fechas de cada archivo interno, si trae `feed_info.txt`, calendario y días
para vencer. **Nunca guarda las URL de redirección ni el mensaje de error
completo** porque llevan token. `mdb-monitor.yml` lo corre cada lunes junto
con `mdb_estado.py`: incluye `setran.json` en el PR (ignora `revisado` y
`dias_para_vencer`) y abre un issue si el enlace falla, si no hay calendario,
si vence en menos de 30 días o si ya venció. Se aprovechó para fijar
`actions/checkout` por SHA, como en los demás workflows.


### 2026-11-14 — Recálculo con el feed de SETRAN
- Solo el AMG: agencias BUS, MM, MMA, MMP, MT, ST y ME. Fuera: PV y PVMT
  (Puerto Vallarta), LGM (Lagos de Moreno) y TEP (Tepabus, Tepatitlán).
- `frequencies.txt` casi vacío (18 renglones): las frecuencias salen de
  `stop_times.txt` (leído en streaming), salida = primera parada del viaje,
  en un miércoles típico (2026-05-06, respetando `calendar_dates`), pico
  07:00–09:00 en el sentido más frecuente. Correr `analisis.py` después de
  `gtfs_a_geojson.py` (escribe `frec_min` en `rutas.geojson`).
- 2024 → 2026: rutas 247 → 332; rutas cada 20 min o más en pico 15 → 51;
  sin servicio nocturno 111 → 128; máximo de rutas en un corredor 35 → 53
  (Calz. Independencia Sur). 96 rutas nuevas y 11 quitadas por `route_id`.
- `paradas.geojson` lista `route_id` (hay nombres cortos repetidos entre
  agencias, p. ej. T01 en MMP y MMA). Todas las rutas traen trazo, así que
  ya no se añade ninguna desde OSM (`rutas_osm.geojson` vacío).
- Problemas del feed: sin `feed_info` ni licencia; `route_long_name` vacío
  (el nombre está en `route_desc`); `route_short_name` con espacios o vacío;
  `route_id` con espacios; MMP sin color; algunas rutas (MT_L2–MT_L4,
  MP-T02, R00000029) traen los dos sentidos con el mismo `direction_id`, así
  que el sentido se distingue también por la parada de salida (antes salían
  a la mitad, p. ej. MT_L4 2 → 5 min). C25 (2 min) y T10 (3 min) no son
  duplicados: así vienen programadas en el feed, con salidas regulares que
  parecen teóricas más que observadas.
