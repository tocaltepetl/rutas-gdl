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
públicos en la PNT. Límite de 20 escrituras por día por IP con una llave
SHA-256(sal + día + IP) en la tabla `limites`; la IP no se guarda y las llaves
de días anteriores se borran en cada escritura. La sal es el secreto opcional
`SAL` (sin él, la llave de una IPv4 se podría revertir por fuerza bruta con
acceso a la base).

**Límites conocidos:** cualquiera que conozca un folio puede cambiar su
estado (no hay cuentas, a propósito); los datos los captura la ciudadanía y
hay que verificarlos en la PNT. **Pendiente:** crear la base
(`wrangler d1 create rutas-gdl`), poner su id en `wrangler.jsonc` y definir
`SAL` con `wrangler secret put SAL`. Las migraciones se aplican en
`release.yml` antes de desplegar.
