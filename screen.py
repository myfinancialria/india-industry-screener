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
from zoneinfo import ZoneInfo

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


def _previous_rows():
    """Flatten the prior published top rows for safe carry-forward on fetch failure."""
    if not os.path.exists(OUT):
        return {}
    try:
        with open(OUT) as f:
            prior = json.load(f)
    except (OSError, ValueError):
        return {}
    rows = {}
    for ind in prior.get("industries", []):
        for row in ind.get("top3", []):
            if row.get("ticker"):
                rows[row["ticker"]] = row
    return rows


def run(log=print):
    run_utc = datetime.now(timezone.utc)
    run_at = run_utc.strftime("%Y-%m-%d %H:%M UTC")
    run_at_ist = run_utc.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M IST")
    all_tickers = [t for ind in INDUSTRIES for t in ind["tickers"]]
    unique_tickers = list(dict.fromkeys(all_tickers))
    log(f"Scraping {len(unique_tickers)} unique tickers across {len(INDUSTRIES)} industries...")
    metrics = scrape_all(unique_tickers, log=log)

    previous = _previous_rows()
    failed_tickers = []
    fresh_count = 0
    carried_count = 0
    for ticker in unique_tickers:
        metric = metrics.get(ticker, {})
        if metric.get("ok"):
            metric["data_status"] = "fresh"
            metric["source_fetched_at"] = run_at
            fresh_count += 1
            continue
        failed_tickers.append(ticker)
        prior = previous.get(ticker)
        if prior:
            carried = dict(prior)
            carried["data_status"] = "carried_forward"
            carried["fetch_error"] = "Latest fetch failed; prior successful snapshot retained."
            metrics[ticker] = carried
            carried_count += 1

    industries_out = []
    fresh_top_count = 0
    carried_top_count = 0
    for ind in INDUSTRIES:
        cands = []
        for ticker in ind["tickers"]:
            metric = metrics.get(ticker, {})
            if not metric.get("ok"):
                continue
            score, passed, fails = evaluate(metric, ind["kind"])
            row = {**metric, "score": score, "passed": passed, "fails": fails}
            cands.append(row)
        cands.sort(key=lambda c: c["score"], reverse=True)
        top3 = cands[:3]
        fresh_top_count += sum(1 for row in top3 if row.get("data_status") == "fresh")
        carried_top_count += sum(1 for row in top3 if row.get("data_status") == "carried_forward")
        industries_out.append({
            "name": ind["name"], "group": ind["group"], "kind": ind["kind"],
            "kpi": ind["kpi"], "note": ind["note"],
            "candidates_fetched": sum(1 for row in cands if row.get("data_status") in ("fresh", "carried_forward")),
            "candidates_fresh": sum(1 for row in cands if row.get("data_status") == "fresh"),
            "candidates_carried_forward": sum(1 for row in cands if row.get("data_status") == "carried_forward"),
            "candidates_total": len(ind["tickers"]),
            "top3": top3,
        })
        names = ", ".join(f"{row['ticker']}({'PASS' if row['passed'] else 'flag'})" for row in top3)
        log(f"  {ind['name']}: {names}")

    if failed_tickers:
        log(f"\nFetch failures ({len(failed_tickers)}): {', '.join(failed_tickers)}")
    source_status = "fresh" if not failed_tickers else (
        "partial refresh with carry-forward" if carried_count else "partial refresh"
    )
    data = {
        "generated_at": run_at,
        "generated_at_ist": run_at_ist,
        "source": "screener.in",
        "source_url": "https://www.screener.in/",
        "source_status": source_status,
        "fresh_count": fresh_count,
        "fresh_top_count": fresh_top_count,
        "carried_forward_count": carried_count,
        "carried_forward_top_count": carried_top_count,
        "failed_count": len(failed_tickers),
        "failed_tickers": failed_tickers,
        "coverage_ratio": round((fresh_count + carried_count) / len(unique_tickers), 3) if unique_tickers else 0,
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
