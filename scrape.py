"""
Scrape fundamental-quality metrics from screener.in company pages.

Only the metrics that a public screener.in company page reliably exposes are
read: Market Cap, Current Price, Stock P/E, ROCE, ROE, 5yr sales CAGR,
5yr profit CAGR, OPM (latest) and Debt/Equity (derived from the balance sheet).

Be polite: a real User-Agent and a delay between requests. Failures are logged
and returned as None so the screen still ranks the tickers that did resolve.
"""
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY = 1.5  # seconds between requests


def _num(text):
    """Parse a screener number like '4,53,138', '20.5 %', '1,253' -> float."""
    if text is None:
        return None
    t = text.replace(",", "").replace("%", "").replace("Cr.", "").strip()
    m = re.search(r"-?\d+\.?\d*", t)
    return float(m.group()) if m else None


def _fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def _top_ratios(soup):
    out = {}
    for li in soup.select("#top-ratios li"):
        name_el = li.select_one(".name")
        val_el = li.select_one(".value")
        if not name_el or not val_el:
            continue
        out[name_el.get_text(strip=True).lower()] = val_el.get_text(" ", strip=True)
    return out


def _ranges(soup):
    """Return dict like {'compounded sales growth': {'5 years': 23.0}, ...}."""
    out = {}
    for table in soup.select("table.ranges-table"):
        th = table.select_one("th")
        if not th:
            continue
        title = th.get_text(strip=True).lower()
        rows = {}
        for tr in table.select("tr"):
            tds = tr.select("td")
            if len(tds) == 2:
                label = tds[0].get_text(strip=True).lower().rstrip(":")
                rows[label] = _num(tds[1].get_text(strip=True))
        out[title] = rows
    return out


def _section_row_latest(soup, section_id, row_label):
    """Latest (last non-empty) value of a named row in a P&L / balance-sheet table."""
    section = soup.select_one(f"#{section_id}")
    if not section:
        return None
    for tr in section.select("tbody tr"):
        cells = tr.select("td")
        if not cells:
            continue
        label = cells[0].get_text(strip=True).lower()
        if label.startswith(row_label.lower()):
            for td in reversed(cells[1:]):
                v = _num(td.get_text(strip=True))
                if v is not None:
                    return v
    return None


def scrape_ticker(ticker):
    """Return a metrics dict for one ticker (values may be None if unavailable)."""
    enc = urllib.parse.quote(ticker, safe="")
    html = _fetch(f"https://www.screener.in/company/{enc}/consolidated/")
    if html is None:
        html = _fetch(f"https://www.screener.in/company/{enc}/")
    if html is None:
        return {"ticker": ticker, "ok": False}

    soup = BeautifulSoup(html, "html.parser")
    top = _top_ratios(soup)
    rng = _ranges(soup)

    sales = rng.get("compounded sales growth", {})
    profit = rng.get("compounded profit growth", {})

    equity = _section_row_latest(soup, "balance-sheet", "Equity Capital")
    reserves = _section_row_latest(soup, "balance-sheet", "Reserves")
    borrow = _section_row_latest(soup, "balance-sheet", "Borrowings")
    de = None
    if borrow is not None and equity is not None and reserves is not None:
        denom = equity + reserves
        de = round(borrow / denom, 2) if denom > 0 else None

    return {
        "ticker": ticker,
        "ok": True,
        "name": (soup.select_one("h1") or soup.new_tag("h1")).get_text(strip=True) or ticker,
        "mcap": _num(top.get("market cap")),
        "price": _num(top.get("current price")),
        "pe": _num(top.get("stock p/e")),
        "roce": _num(top.get("roce")),
        "roe": _num(top.get("roe")),
        "sales_cagr_5y": sales.get("5 years"),
        "profit_cagr_5y": profit.get("5 years"),
        "opm": _section_row_latest(soup, "profit-loss", "OPM"),
        "de": de,
    }


def scrape_all(tickers, log=print):
    seen, results = set(), {}
    for t in tickers:
        if t in seen:
            continue
        seen.add(t)
        m = scrape_ticker(t)
        results[t] = m
        status = "ok" if m.get("ok") else "FAIL"
        log(f"  [{status}] {t:<14} ROCE={m.get('roce')} ROE={m.get('roe')} "
            f"sales5y={m.get('sales_cagr_5y')} profit5y={m.get('profit_cagr_5y')} DE={m.get('de')}")
        time.sleep(REQUEST_DELAY)
    return results


if __name__ == "__main__":
    import json, sys
    tk = sys.argv[1:] or ["SUNPHARMA", "ICICIBANK", "DIXON"]
    print(json.dumps(scrape_all(tk), indent=2))
