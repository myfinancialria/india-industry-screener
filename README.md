# India Industry Screener

An automated, educational **quantitative stock screen**: for each of ~29 Indian
listed industries it ranks the **top 3 companies** on fundamental-quality
metrics scraped from [screener.in](https://www.screener.in), and publishes the
result as a static webpage that refreshes **daily** via GitHub Actions → GitHub Pages, with a planned run around 08:00 IST.

> ⚠️ **Not investment advice.** This is an educational tool and the output of a
> mechanical screen. It contains no buy/sell/target calls, is not a
> recommendation or solicitation, and the author is **not** a SEBI-registered
> Research Analyst or Investment Adviser. Rankings may contain data errors. Do
> your own research and consult a SEBI-registered adviser before any decision.

## What it screens

**Base quality filter:** ROCE ≥ 15%, ROE ≥ 15%, 5yr sales CAGR ≥ 10%,
5yr profit CAGR ≥ 12%, Debt/Equity ≤ 1.

Ranking adapts per industry `kind`:

| kind | ranking basis | why |
|------|---------------|-----|
| `general` | ROCE + ROE + growth, must pass filter for a PASS badge | standard quality compounders |
| `financial` | ROE + profit/sales growth | ROCE/OPM/D-E are meaningless for lenders |
| `cyclical` | relative strength | metals/cement/power/oil&gas structurally fail the filter |
| `realestate` | growth (pre-sales proxy) | revenue-recognition lag makes returns fail by design |

Sector-specific KPIs (ROA, NIM, GNPA, combined ratio, ARPOB, EBITDA/tonne,
pre-sales, order book) are shown as **static analyst context** — they are not on
screener.in's standard pages and are not scraped.

## Files

| file | role |
|------|------|
| `universe.py` | industry definitions, candidate tickers, filter config |
| `scrape.py` | polite screener.in scraper (ROCE, ROE, CAGRs, OPM, D/E) |
| `screen.py` | applies filters, ranks top 3, writes `docs/data.json` |
| `generate_site.py` | renders `docs/index.html` from the JSON |
| `.github/workflows/screen.yml` | daily cron + auto-commit + Pages deploy |

## Run locally

```bash
pip install -r requirements.txt
python screen.py          # scrape + rank -> docs/data.json
python generate_site.py   # -> docs/index.html
open docs/index.html
```

## Automation

`screen.yml` runs on `cron: "30 2 * * *"` (~08:00 IST daily), regenerates the data + page, commits `docs/`, and GitHub Pages serves it. GitHub may delay scheduled jobs slightly; the page shows the last refresh time and fetch status. Temporary source failures are labelled and prior successful top rows can be carried forward rather than silently disappearing. Trigger manually anytime from the Actions tab (`workflow_dispatch`).

## Data source & etiquette

Metrics are read from public screener.in company pages with a real User-Agent and
a delay between requests. This is a low-volume, twice-monthly read for personal
educational use. Respect screener.in's terms of service.


## Dashboard additions

The published page now includes candidate coverage, fresh versus carried-forward row status, source links for every company, current price and score columns, searchable company/ticker filtering, industry-type and quality-state filters, a daily refresh contract, and a transparent list of fetch failures. These are presentation and data-quality aids; they do not turn the screen into investment advice.
