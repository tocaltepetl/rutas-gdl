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
