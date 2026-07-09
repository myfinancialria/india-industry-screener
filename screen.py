"""
Apply per-industry filters to scraped metrics and pick the top 3 per industry.

Writes docs/data.json consumed by generate_site.py.

The ranking uses only fundamental-quality metrics scraped from screener.in:
  ROCE, ROE, 5yr sales CAGR, 5yr profit CAGR, OPM, Debt/Equity.
Ranking logic varies by industry 'kind' (general / financial / cyclical /
realestate) because ROCE/OPM/D-E are not meaningful for lenders, and cyclical /
real-estate sectors structurally fail the quality filter.
"""
import json
import os
from datetime import datetime, timezone

from universe import INDUSTRIES, BASE_FILTER
from scrape import scrape_all

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "docs", "data.json")


def n(x):
    return x if isinstance(x, (int, float)) else 0.0


def evaluate(m, kind):
    """Return (score, passed, fails) for one candidate under an industry kind."""
    roce, roe = m.get("roce"), m.get("roe")
    sales, profit, de = m.get("sales_cagr_5y"), m.get("profit_cagr_5y"), m.get("de")
    fails = []

    if kind == "financial":
        # ROCE / OPM / D-E are not meaningful for lenders.
        if n(roe) < BASE_FILTER["roe_min"]:
            fails.append("ROE<15")
        if n(profit) < BASE_FILTER["profit_cagr_min"]:
            fails.append("profit5y<12")
        if n(sales) < BASE_FILTER["sales_cagr_min"]:
            fails.append("sales5y<10")
        score = n(roe) * 1.5 + n(profit) + n(sales)

    elif kind == "realestate":
        # Returns fail by design; rank on growth (pre-sales proxy) + any ROCE.
        if n(roce) < BASE_FILTER["roce_min"]:
            fails.append("ROCE<15")
        if n(roe) < BASE_FILTER["roe_min"]:
            fails.append("ROE<15")
        score = n(sales) + n(profit) + n(roce) * 0.3 + n(roe) * 0.3

    else:  # general or cyclical
        if n(roce) < BASE_FILTER["roce_min"]:
            fails.append("ROCE<15")
        if n(roe) < BASE_FILTER["roe_min"]:
            fails.append("ROE<15")
        if n(sales) < BASE_FILTER["sales_cagr_min"]:
            fails.append("sales5y<10")
        if n(profit) < BASE_FILTER["profit_cagr_min"]:
            fails.append("profit5y<12")
        if de is not None and de > BASE_FILTER["de_max"]:
            fails.append("D/E>1")
        score = n(roce) + n(roe) + 0.5 * (n(sales) + n(profit))

    return round(score, 1), (len(fails) == 0), fails


def run(log=print):
    all_tickers = [t for ind in INDUSTRIES for t in ind["tickers"]]
    log(f"Scraping {len(set(all_tickers))} unique tickers across {len(INDUSTRIES)} industries...")
    metrics = scrape_all(all_tickers, log=log)

    industries_out = []
    for ind in INDUSTRIES:
        cands = []
        for t in ind["tickers"]:
            m = metrics.get(t, {})
            if not m.get("ok"):
                continue
            score, passed, fails = evaluate(m, ind["kind"])
            cands.append({**m, "score": score, "passed": passed, "fails": fails})
        cands.sort(key=lambda c: c["score"], reverse=True)
        top3 = cands[:3]
        industries_out.append({
            "name": ind["name"], "group": ind["group"], "kind": ind["kind"],
            "kpi": ind["kpi"], "note": ind["note"],
            "candidates_fetched": len(cands), "candidates_total": len(ind["tickers"]),
            "top3": top3,
        })
        names = ", ".join(f"{c['ticker']}({'PASS' if c['passed'] else 'flag'})" for c in top3)
        log(f"  {ind['name']}: {names}")

    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "base_filter": BASE_FILTER,
        "industry_count": len(industries_out),
        "industries": industries_out,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)
    log(f"\nWrote {OUT}")
    return data


if __name__ == "__main__":
    run()
