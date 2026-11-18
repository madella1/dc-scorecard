# DC Scorecard

**A report card for DC, block by block.**

DC Scorecard grades the District of Columbia and each of its 8 wards, 46 Advisory Neighborhood Commissions (ANCs) and 345 single-member districts using the city's own public data. Each grade shows where an area stands today and whether it is getting better or worse.

**Live site:** https://dcscorecard.org

The first scorecard covers **traffic safety**. Others are planned: public safety, city services (311), affordability, growth, land use, fiscal health and, eventually, resident satisfaction.

DC Scorecard is an independent, nonpartisan volunteer project. It is not affiliated with the DC government.

---

## The traffic safety scorecard

For every area, the scorecard shows:

- **A safety grade (A to F) with a plus or minus.** The letter compares an area's harm with DC as a whole. The sign shows whether it is improving or worsening faster than DC over the last two years.
- **Four measures**, as 2023 to 2025 yearly averages:
  - crashes
  - people seriously injured or killed
  - pedestrians injured or killed
  - cyclists injured or killed
- **Traffic deaths**, for wards and the city only. There are too few deaths to compare smaller areas fairly.
- **Four ways to compare:**
  - per district (about 2,000 residents, so effectively per resident)
  - in total
  - per square mile
  - per 100 million vehicle miles driven
- **Trends since 2019**, plus 2026 so far compared with the same months of 2025.
- **A city grade** comparing DC's traffic deaths per resident with the 26 other US cities of 500,000 to 1 million people.

### How the grades work

| Grade | Harm compared with DC |
|---|---|
| A | Half the DC rate or less |
| B | 50% to 80% of the DC rate |
| C | Within 25% of the DC average |
| D | 1.25 to 2 times the DC rate |
| F | More than twice the DC rate |

Harm combines three measures:

| Measure | Weight |
|---|---|
| Serious injuries and deaths per district | 40% |
| Pedestrians and cyclists injured or killed per district | 40% |
| Crashes per vehicle mile on DDOT-counted streets, excluding freeways | 20% |

Cutoffs are fixed, not curved, so every area can earn an A as DC gets safer. Areas with only a few cases are pulled partway toward the DC average, so a single bad crash can't sink a grade.

The **plus or minus** compares crashes and people hurt in the last two years with the two years before:
- **Plus:** at least 12% better than DC's change.
- **Minus:** at least 12% worse than DC's change.

The full method, with its limits, is on the site's **About this scorecard** tab.

---

## Data sources

| Data | Source |
|---|---|
| Crashes in DC (Metropolitan Police Department crash reports) | [DC Open Data](https://opendata.dc.gov) |
| Single Member District 2023 boundaries | DC Open Data |
| Ward 2022 boundaries | DC Open Data |
| Traffic Volume 2025 (average annual daily traffic) | DDOT via DC Open Data |
| Roadway Functional Classification | DDOT via DC Open Data |
| Peer city traffic death rates, 2008 to 2012 and 2018 to 2022 | Schneider, Barbee, Nelson and Gu, "[Examining a Lost Decade for Traffic Safety in Large US Cities](https://findingspress.org/article/155976-examining-a-lost-decade-for-traffic-safety-in-large-us-cities)," *Findings* (2026), from NHTSA's Fatality Analysis Reporting System |

Crash data currently runs through October 19, 2026.

---

## What's in this repository

```
index.html                 Home page
traffic-safety/            The traffic safety scorecard
about/                     About the project
assets/                    Styles, fonts (Public Sans), d3 charting library, data loader
data/traffic-safety/       The scorecard's data as CSV and JSON files, free to download and reuse
pipeline/                  Python scripts that turn the source downloads into the data files
```

The site is plain HTML, CSS and JavaScript, with no build step or server. GitHub Pages serves the files as they are.

### Using the data

The CSV files in `data/traffic-safety/` hold every number on the site:

| File | Contents |
|---|---|
| `dc-crashes-by-smd.csv` | One row per single-member district |
| `dc-crashes-by-anc.csv` | One row per ANC |
| `dc-crashes-by-ward.csv` | One row per ward |
| `dc-crashes-city.csv` and `dc-crashes-citywide.csv` | DC as a whole |
| `dc-peer-cities.csv` | Traffic death rates for the 27 peer cities |

Each area file includes grades, measures, ranks and yearly counts. If you use them, please credit DC Open Data and DDOT as the sources and DC Scorecard as the compiler.

### Viewing the site on your computer

Download or clone the repository, then open `index.html` in a browser. It works straight from the folder. To preview it exactly as it runs online, start a local server in the folder:

```
python3 -m http.server
```

Then visit http://localhost:8000.

### Rebuilding the data

The scripts in `pipeline/` run in this order. They need Python 3 with the `shapely` package.

| Script | What it does |
|---|---|
| `process.py` | Places each crash in its district and computes traffic volume per district |
| `build.py` | Builds the ward, ANC, district and city tables, and the map outlines |
| `trend.py` | Counts crashes in the last two years and the two years before, for the plus or minus |
| `grade.py` | Computes the letter grades and the city's peer comparison |
| `build_site.py` | Assembles the website folder |

The scripts were written for this project's own runs, so file paths may need adjusting. Each script's first lines explain its inputs.

---

## Limits

- Only police-reported crashes are included, so minor crashes are undercounted.
- Police records can miss someone who dies days after a crash, so death counts may run slightly below DC's official totals.
- Busy commuter roads raise an area's counts no matter what residents do. The per vehicle mile view helps separate road risk from traffic volume.
- The city grade uses peer death rates through 2022, the latest in the published study.
- Grades show where harm happens, not why.

---

## Contact

Questions, corrections or ideas for new measures are welcome. Please [open an issue](https://github.com/madella1/dc-scorecard/issues) on this repository.
