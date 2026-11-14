# Comparación GTFS oficial vs. OpenStreetMap

Generado por `scripts/osm_rutas.py` el 2026-11-14, con datos OSM al 2026-11-14.
Datos OSM © colaboradores de OpenStreetMap, ODbL.

- Relaciones de ruta en OSM en la zona: 258 (128 `ref` distintos); descartadas: 1.
- Rutas en el GTFS: 276; con trazo: 247; sin trazo: 29.
- Agregadas al mapa desde OSM: 2 nuevas y 0 que completan rutas del GTFS sin trazo.

La comparación es por `ref` exacto: `C12` en OSM no es `C12-V1` del GTFS. Algunas
«nuevas» pueden ser la misma ruta con otra clave; conviene revisarlas a mano.

## Rutas en OSM que no están en el GTFS

| ref | nombre en OSM | relaciones | última edición | antigüedad |
|---|---|---|---|---|
| MP-T04 | Mi Macro Periférico Troncal 4 | [21360782](https://www.openstreetmap.org/relation/21360782), [21360783](https://www.openstreetmap.org/relation/21360783) | 2026-09-06 | 2 meses |
| TL-4 | Linea 4 (Tlajomulco Centro → Las Juntas) | [19978278](https://www.openstreetmap.org/relation/19978278), [19978279](https://www.openstreetmap.org/relation/19978279) | 2026-10-23 | 0 meses |

## Rutas del GTFS sin trazo que sí están en OSM

| ref | nombre en OSM | relaciones | última edición | antigüedad |
|---|---|---|---|---|

Están en OSM pero sin trazo (solo paradas): T06-03, T07-C01, T13A-C01, T13A-C02, T13A-C03, T13B-C01-1, T13B-V1, T13B-V2, T13C-1, T13C-2, T14A-C02, T16B-1, T16B-C01, T16B-C03, T17-1.

Siguen sin trazo en ninguna fuente (14): C119, C63, T07-C04, T13B-C02-1, T14A-C01, T14A-C03, T15-1, T15-C01, T15-C02, T15-C03, T15-C04, T15-C05, T15-C06, T16A-C01.

## En OSM y no en el GTFS, pero sin trazo (solo paradas; no se muestran)

| ref | nombre en OSM | relaciones | última edición | antigüedad |
|---|---|---|---|---|
| 175-Roca | 175-Roca | [14302770](https://www.openstreetmap.org/relation/14302770), [14302852](https://www.openstreetmap.org/relation/14302852) | 2022-06-28 | 4 años |
| C11 | C11 | [14308854](https://www.openstreetmap.org/relation/14308854), [14308865](https://www.openstreetmap.org/relation/14308865) | 2022-06-30 | 4 años |
| C12 | C12 | [14989049](https://www.openstreetmap.org/relation/14989049) | 2023-06-20 | 3 años |
| C14 | C14 - 175A | [13990900](https://www.openstreetmap.org/relation/13990900), [14017311](https://www.openstreetmap.org/relation/14017311) | 2022-12-10 | 3 años |
| MP-A05-2 | Alimentadora Mi Macro Periférico A05-2 | [14012587](https://www.openstreetmap.org/relation/14012587), [14036349](https://www.openstreetmap.org/relation/14036349) | 2026-10-09 | 1 meses |
| ST-L1B | SiTren L1B | [14302608](https://www.openstreetmap.org/relation/14302608), [14302626](https://www.openstreetmap.org/relation/14302626) | 2023-06-26 | 3 años |
| T13A-1 | T13A-1 | [14052671](https://www.openstreetmap.org/relation/14052671), [14052694](https://www.openstreetmap.org/relation/14052694) | 2022-06-28 | 4 años |
| T19-C06 | T19-C06 | [14311366](https://www.openstreetmap.org/relation/14311366), [14311472](https://www.openstreetmap.org/relation/14311472) | 2024-07-23 | 2 años |
| T13B-C02 | T13B-C02 | [14305637](https://www.openstreetmap.org/relation/14305637), [14305673](https://www.openstreetmap.org/relation/14305673) | 2026-09-15 | 2 meses |
| T13C-C04 | T13C-C04 | [14305772](https://www.openstreetmap.org/relation/14305772), [14305774](https://www.openstreetmap.org/relation/14305774) | 2022-06-29 | 4 años |
| T18-Lopez | T18-Lopez | [14012781](https://www.openstreetmap.org/relation/14012781), [14305005](https://www.openstreetmap.org/relation/14305005) | 2022-06-28 | 4 años |
| T13B-C01-2 | T13B-C01-2 | [14305584](https://www.openstreetmap.org/relation/14305584), [14305596](https://www.openstreetmap.org/relation/14305596) | 2026-09-15 | 2 meses |
| T18-Terranova | T18-Terranova | [14305070](https://www.openstreetmap.org/relation/14305070), [14305112](https://www.openstreetmap.org/relation/14305112) | 2022-06-28 | 4 años |

Muchas relaciones de la zona (importadas en 2022) solo tienen paradas, sin las
calles del recorrido. Completarlas en OSM las haría aparecer aquí.

## Antigüedad de las relaciones OSM (año de última edición)

- 2022: 150
- 2023: 5
- 2024: 32
- 2025: 9
- 2026: 62

## Descartadas

- [14310983](https://www.openstreetmap.org/relation/14310983) Safari Masai Mara (sin ref)
