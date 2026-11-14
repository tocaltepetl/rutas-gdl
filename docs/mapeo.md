# Jornada de mapeo: rutas de camión en OpenStreetMap

*Actualizado el 2026-11-14:* SETRAN publica desde el 30 de septiembre de 2026
un GTFS vigente (vía Ualabee) que ya trae las 58 rutas que faltaban en el de
marzo de 2024, y el mapa de este sitio lo usa. Pero ese archivo **no tiene
licencia explícita**, así que no se puede copiar a OSM. Mapear en OpenStreetMap
sigue sirviendo para tener las rutas como dato abierto de verdad (licencia
ODbL), corregir errores y no depender de un solo proveedor. En noviembre de
2026 había 251 relaciones de rutas de camión en la ZMG; solo 54 se editaron
en 2026.

> **Regla de oro:** mapea lo que tú viste o recorriste. **No copies** trazos ni
> paradas de Google Maps, Moovit, Treep/Ualabee, del GTFS de SETRAN (no tiene
> licencia explícita) ni de ninguna app: no tienen licencia compatible y OSM
> los borra. La lista de abajo solo dice *qué* falta.

## Antes de empezar
- Crea una cuenta en <https://www.openstreetmap.org/user/new>.
- Si es tu primera vez, haz el tutorial de iD (aparece al abrir el editor).
- Lee la [wiki de rutas de autobús](https://wiki.openstreetmap.org/wiki/ES:Buses)
  y el [esquema public_transport v2](https://wiki.openstreetmap.org/wiki/Proposed_features/Public_Transport).

## Cómo se mapea una ruta (PTv2)

Una ruta es una **relación** con:

| Etiqueta | Valor en GDL | Nota |
|---|---|---|
| `type` | `route` | |
| `route` | `bus` | `trolleybus` para Mi Transporte Eléctrico |
| `public_transport:version` | `2` | |
| `ref` | `C111-2`, `T13B-C01`… | el identificador de SETRAN, tal cual |
| `name` | `Ruta C111-2: Origen → Destino` | formato `Ruta <ref>: <desde> → <hasta>` |
| `from` / `to` | nombres de las terminales | |
| `network` | `Mi Transporte` · `Mi Macro` | el que se usa hoy en GDL |
| `operator` | `Setran` (Mi Transporte) · `SITEUR` (Mi Macro, alimentadoras) | revisa qué usan las relaciones vecinas y sé consistente |
| `colour` | color oficial, p. ej. `#4C8D2B` | opcional |

- **Una relación por sentido** (ida y vuelta). Agrúpalas en una relación
  `type=route_master` + `route_master=bus` con el mismo `ref`, `network` y
  `operator`.
- **Miembros, en orden:** primero las paradas (rol `stop` para el punto en la
  vía o `platform` para el poste/andén), en el orden del recorrido; después las
  vías (rol vacío) desde la terminal de salida hasta la de llegada, sin huecos.
- **Paradas:** nodo `highway=bus_stop` + `public_transport=platform` + `bus=yes`
  junto a la vía, con `name` si hay letrero. Agrega `shelter=yes/no`,
  `bench=yes/no`, `tactile_paving`, `lit` si los ves: sirven para analizar
  accesibilidad.
- Si una vía de un solo sentido tiene sentido equivocado o le falta
  `oneway=yes`, el validador marcará la ruta como rota: arregla la calle.

## Herramientas
- **iD** (el editor web de openstreetmap.org): bien para paradas y para
  agregar vías a una relación existente. Con relaciones largas se vuelve lento.
- **JOSM** con el complemento **PT_Assistant**: la mejor opción para crear y
  validar rutas completas (ordena miembros, detecta huecos y sentidos).
- **StreetComplete** (Android) y **Every Door** (Android/iOS): para levantar
  paradas, refugios y bancas caminando, sin saber editar.
- **Trazas GPS**: graba tu propio viaje en camión con OsmAnd, OSMTracker
  (Android) u Open GPX Tracker (iOS) y súbela en
  <https://www.openstreetmap.org/traces>. Luego, en iD o JOSM, cárgala como capa
  de fondo para seguir el recorrido real. Anota en papel o en la app dónde
  para el camión.

## Privacidad de tus trazas
- Una traza GPS revela dónde vives, trabajas o estudias. **Empieza a grabar
  después de salir de tu casa y detenla antes de llegar** (o recorta el
  principio y el final antes de subirla).
- Al subirla, elige la visibilidad **«Identificable»** solo si estás de
  acuerdo; **«Privada»** o **«Trazable»** sirven igual para mapear y no
  muestran tu nombre ni el orden de los puntos con horas.
- No subas trazas de otras personas ni fotos con caras o placas.
- Más: [política de privacidad común](https://github.com/tocaltepetl/.github/blob/main/docs/privacidad.md).

## Cómo coordinarnos
- Cada ruta tiene (o tendrá) un issue en
  <https://github.com/tocaltepetl/rutas-gdl/issues> con la etiqueta **`mapeo`**.
  Asígnatelo o comenta «la tomo» antes de empezar, para no duplicar.
- Al terminar, pega en el issue el enlace a la relación de OSM y a tu
  changeset, y ciérralo.
- En el comentario del changeset escribe algo como
  `Ruta C111-2 (Mi Transporte), recorrida el 2026-11-20 #rutasgdl`
  y como fuente `source=survey;gps`.
- Dudas de etiquetado: pregunta en el issue o en la comunidad de OSM México.

## Rutas nuevas a mapear (58)

Identificadores de Mi Transporte que aparecen en listas recientes
(`datos/lineas-treep-mi-transporte.txt`, consultado el 2026-11-14) y **no**
están en el GTFS 2024 (`routes.txt`, agencia Mi Transporte). Varias son variantes de
rutas existentes (`-V1`, `-C01`, sufijos con destino): conviene revisar si en
OSM ya existe la ruta madre y partir de ahí. Antes de mapear, comprueba en la
calle o en el letrero del camión el número y destino exactos.

| # | Identificador | # | Identificador |
|---|---|---|---|
| 1 | C111-2 | 30 | T11B-C01 Tonala Centro |
| 2 | C119 EALM | 31 | T13A-5 Agaves |
| 3 | C119 JGLM | 32 | T13A-6 Zapote-Aeropuerto |
| 4 | C12 | 33 | T13A-C02 Cima Serena |
| 5 | C121A Avila Camacho | 34 | T13A-C02 Purisima |
| 6 | C128A V2 | 35 | T13A-C03 Rancho Alegre |
| 7 | C15 Reyes Heroles | 36 | T13B Azucena |
| 8 | C35 Colinas de Tonala | 37 | T13B Lilas |
| 9 | C51-V1 | 38 | T13B-1 Jardines |
| 10 | C52 | 39 | T13B-1 Villas |
| 11 | C58 | 40 | T13B-C01 |
| 12 | C58 CU Tonala | 41 | T13B-C02 |
| 13 | C62 Santibanez | 42 | T13C |
| 14 | C71 Preparatoria #2 | 43 | T13C-C01 Ctral de Autobuses |
| 15 | C72 | 44 | T13C-C01 P del Triunfo |
| 16 | C81-1 | 45 | T13C-C02 Faro-Clin No. 14 |
| 17 | C81-2 | 46 | T13C-C02 Faro-Ctral de Auto |
| 18 | C84 | 47 | T13C-C02 Villas Andalucia |
| 19 | C87 | 48 | T14A-C04 San  Sebastianito |
| 20 | C96-V1 | 49 | T14A-C04 Vista Hermosa |
| 21 | R00000001 | 50 | T14B-C02 Benito Juarez |
| 22 | R00000002 | 51 | T15-C06 Andares |
| 23 | T06-2 | 52 | T15-C06 Hospital Civil |
| 24 | T08-C02 | 53 | T16B-C04 |
| 25 | T09-C1 Oblatos - Belisario | 54 | T16B-C05 |
| 26 | T09-C1 Oblatos - Circunv | 55 | T21 |
| 27 | T09-C2 Belisario | 56 | T21-C01 Zapotlanejo |
| 28 | T09-C2 Circunv | 57 | T22 V05 |
| 29 | T10-C03-V2 | 58 | T22-V02 |

`R00000001` y `R00000002` parecen identificadores provisionales: no se mapean
hasta saber a qué ruta corresponden.

Para regenerar la lista (con el GTFS descomprimido en `/tmp/gtfs`):

```sh
grep -v '^#' datos/lineas-treep-mi-transporte.txt | sort -u > /tmp/recientes.txt
awk -F, 'NR>1 && $2=="BUS" {print $1}' /tmp/gtfs/routes.txt | sort -u > /tmp/gtfs2024.txt
comm -23 /tmp/recientes.txt /tmp/gtfs2024.txt
```
