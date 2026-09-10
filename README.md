# 178 First Avenue and 115 Avenue A, foot traffic

Two East Village storefronts 307 m apart, one on First Avenue at 11th Street, one on Avenue A facing Tompkins Square Park. Public data, gathered 9 September 2026.

**Live page:** https://feldtdesign-ship-it.github.io/east-village-178-115/

- `index.html` – the pair. One hour-scrubber drives the page: the L at 1st Avenue as the shared pump, a card per door, the block map drawn from OpenStreetMap geometry, the day, the week, the years since 2020, weather, the city's counts, both sidewalks, and what is left to buy.
- `live-wall.html` – the six nearest NYC DOT cameras. Two look down First Avenue from 14th Street.
- `data/` – the raw pulls: MTA subway hourly ridership for 1st Av (complex 119) and Astor Pl (407), MTA bus stop-level ridership for the ten stops nearest the doors, Open-Meteo weather, curb geometry, the block map.
- `frames/` – camera frames from the evening of 9 September 2026.
- `build/` – the script and template that turn the data into the page.

## Where the numbers come from

- MTA subway hourly ridership, data.ny.gov, complexes 119 and 407
- MTA bus stop-level hourly ridership, data.ny.gov
- NYC Motor Vehicle Collisions
- NYC Planimetric Database curbs, OpenStreetMap, PLUTO: the sidewalks and the lots
- NYC DOT camera network
- Open-Meteo daily archive

Nobody counts the people passing either door. The page says so where it matters.
