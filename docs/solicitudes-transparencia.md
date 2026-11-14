# Solicitudes de acceso a la información — SETRAN y SITEUR

**Dónde:** Plataforma Nacional de Transparencia (https://www.plataformadetransparencia.org.mx),
estado Jalisco, sujeto obligado **Secretaría de Transporte del Estado de Jalisco**.
**Modalidad de entrega:** electrónica, por la plataforma o enlace de descarga.
**Formato:** archivos digitales en su formato original (no escaneos ni PDF de tablas).

---

## Texto para pegar

Con fundamento en el artículo 6.º de la Constitución Política de los Estados
Unidos Mexicanos y en la Ley de Transparencia y Acceso a la Información Pública
del Estado de Jalisco y sus Municipios, solicito la siguiente información:

1. **GTFS estático vigente.** Los archivos GTFS (Especificación General de
   Feeds de Transporte Público) más recientes de las rutas de transporte
   público de la Zona Metropolitana de Guadalajara, incluidos los que la
   Secretaría entregó a Google para la publicación de 275 rutas en Google Maps
   anunciada en julio de 2026. Solicito el archivo .zip tal como se generó.

2. **Datos en tiempo real.** La dirección (URL) de los feeds GTFS-Realtime
   (Vehicle Positions, Trip Updates y Service Alerts) de las rutas que ya
   cuentan con localización GPS, y las condiciones para acceder a ellos. Si no
   existe una dirección pública, solicito saber a qué personas físicas o
   morales se les ha dado acceso y bajo qué condiciones.

3. **Convenio con Ualabee.** Copia en versión pública del convenio, contrato o
   instrumento jurídico celebrado con Ualabee (o la razón social que
   corresponda) para la digitalización de rutas y la localización en tiempo
   real, con sus anexos técnicos, monto, vigencia y las cláusulas sobre
   propiedad, licencia y uso de los datos generados.

4. **Propiedad y apertura de los datos.** Documento que indique quién es
   titular de los datos de rutas, paradas, horarios y posiciones GPS generados
   en ese proyecto, y si la Secretaría tiene previsto publicarlos como datos
   abiertos en datos.jalisco.gob.mx. En su caso, la fecha prevista.

5. **Cobertura del GPS.** Relación de rutas y número de unidades que a la
   fecha de esta solicitud transmiten su ubicación en tiempo real.

6. **Licencia del GTFS publicado.** La licencia de uso del conjunto
   «Actualización de rutas de transporte público colectivo y masivo en la Zona
   Metropolitana de Guadalajara» publicado en datos.jalisco.gob.mx
   (archivo `gtfs_amg_20240312.zip`), y la dirección vigente del portal, que
   el 14 de noviembre de 2026 no estaba disponible.

Cabe señalar que la información del punto 1 ya está a disposición del
público a través de terceros: el sitio https://treep.app/index/agency/35/BUS
muestra 275 líneas de Mi Transporte, con identificadores, recorridos y
paradas que coinciden con el formato del GTFS de la Secretaría y que incluyen
rutas ausentes en la versión de 2024 publicada en datos.jalisco.gob.mx. Al
haberse compartido con particulares que la difunden, no hay razón para no
publicarla como dato abierto.

Para los puntos 1, 2, 5 y 6 solicito la información en formato abierto y
legible por máquina, conforme a los principios de datos abiertos que
establece la ley. Si alguna parte se considera reservada o confidencial,
solicito la versión pública del resto y la prueba de daño correspondiente.

---

## Segunda solicitud: SITEUR

**Sujeto obligado:** Sistema de Tren Eléctrico Urbano (SITEUR). Misma
plataforma, modalidad y formato.

Con fundamento en el artículo 6.º de la Constitución Política de los Estados
Unidos Mexicanos y en la Ley de Transparencia y Acceso a la Información Pública
del Estado de Jalisco y sus Municipios, solicito:

1. Los archivos GTFS (estáticos) de las rutas y líneas que opera o supervisa
   SITEUR (Mi Tren, Mi Macro Calzada, Mi Macro Periférico, Si Tren,
   alimentadoras y demás), en su versión más reciente.
2. La documentación técnica de la fuente de posiciones en tiempo real que
   alimenta la aplicación «Mi Ruta» (miruta.siteur.gob.mx): formato, frecuencia
   de actualización y rutas cubiertas.
3. Si existe o se prevé un feed público en formato GTFS-Realtime (Vehicle
   Positions, Trip Updates, Service Alerts) con esa información, su dirección
   y condiciones de uso; si no existe, las razones y si está previsto
   publicarlo como dato abierto.
4. El contrato o convenio con el proveedor del sistema de localización y de la
   aplicación «Mi Ruta», en versión pública, incluidas las cláusulas sobre
   titularidad y licencia de los datos.

Solicito los puntos 1 y 3 en formato abierto y legible por máquina. Si alguna
parte se considera reservada o confidencial, solicito la versión pública del
resto y la prueba de daño correspondiente.

---

## Notas (no van en la solicitud)
- Plazo legal de respuesta: revisarlo en la ley vigente y anotar la fecha de
  vencimiento al enviarla.
- Si la respuesta es negativa o incompleta, procede el recurso de revisión
  ante el órgano garante de Jalisco (era el ITEI; con la reforma de 2025 que
  extinguió los órganos autónomos de transparencia pudo cambiar: verificar).
- Los puntos 1 y 2 son los que desbloquean el proyecto; los demás sirven para
  argumentar la apertura si se niegan.
- Si llega el GTFS: actualizar `public/data/` con `scripts/gtfs_a_geojson.py`
  y anotarlo en `docs/decisiones.md`.
