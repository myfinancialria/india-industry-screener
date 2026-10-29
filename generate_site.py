"""
Render docs/index.html from docs/data.json — a self-contained, responsive,
theme-aware static page for GitHub Pages.

Framed strictly as an educational quantitative screen: factual metrics only,
no buy/sell/target language, prominent 'not investment advice' disclaimer.
"""
import json
import os
from html import escape
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "docs", "data.json")
OUT = os.path.join(HERE, "docs", "index.html")


def fmt(v, suffix="", dash="—"):
    if not isinstance(v, (int, float)):
        return dash
    if suffix == "cr":
        return f"₹{v:,.0f} cr"
    return f"{v:g}{suffix}"


def metric_cell(v, suffix, good=None):
    txt = fmt(v, suffix)
    cls = ""
    if good is not None and isinstance(v, (int, float)):
        cls = " ok" if good(v) else " weak"
    return f'<td class="num{cls}">{txt}</td>'


def render_row(c):
    ticker = escape(c["ticker"])
    status = c.get("data_status", "fresh")
    if status == "carried_forward":
        status_badge = '<span class="badge carry" title="Latest fetch unavailable; showing the previous successful snapshot">carried forward</span>'
    elif status == "fresh":
        status_badge = '<span class="badge fresh">fresh</span>'
    else:
        status_badge = '<span class="badge carry">status unknown</span>'
    badge = ('<span class="badge pass">PASS</span>' if c["passed"]
             else f'<span class="badge flag" title="{escape(", ".join(c["fails"]))}">flagged</span>')
    fails = f'<div class="fails">misses: {escape(", ".join(c["fails"]))}</div>' if c["fails"] else ""
    source = f'https://www.screener.in/company/{quote(c["ticker"], safe="")}/consolidated/'
    return f"""<tr class="company-row" data-search="{escape((c.get("ticker") or "") + " " + (c.get("name") or ""))}" data-status="{status}">
      <td class="tk"><a class="sym" href="{source}" target="_blank" rel="noopener">{ticker}</a>{badge}{status_badge}
        <div class="cname">{escape(c.get("name") or "")}</div>{fails}</td>
      {metric_cell(c.get("price"), "₹")}
      {metric_cell(c.get("mcap"), "cr")}
      {metric_cell(c.get("roce"), "%", lambda v: v >= 15)}
      {metric_cell(c.get("roe"), "%", lambda v: v >= 15)}
      {metric_cell(c.get("sales_cagr_5y"), "%", lambda v: v >= 10)}
      {metric_cell(c.get("profit_cagr_5y"), "%", lambda v: v >= 12)}
      {metric_cell(c.get("opm"), "%")}
      {metric_cell(c.get("de"), "", lambda v: v <= 1)}
      {metric_cell(c.get("pe"), "")}
      <td class="num score">{fmt(c.get("score"))}</td>
    </tr>"""


def render_industry(ind):
    rows = "".join(render_row(c) for c in ind["top3"]) or \
        '<tr><td colspan="10" class="empty">No data fetched this run.</td></tr>'
    kind_tag = f'<span class="kind {ind["kind"]}">{ind["kind"]}</span>'
    pass_count = sum(1 for c in ind["top3"] if c.get("passed"))
    carry_count = sum(1 for c in ind["top3"] if c.get("data_status") == "carried_forward")
    carry_note = f' · {carry_count} carried forward' if carry_count else ""
    return f"""<section class="ind" id="{quote(ind["name"].lower().replace(" ", "-"), safe="-")}" data-kind="{ind["kind"]}" data-industry="{escape(ind["name"])}">
      <div class="ind-head">
        <h3>{escape(ind["name"])} {kind_tag}</h3>
        <span class="cov">{ind["candidates_fetched"]}/{ind["candidates_total"]} screened · {pass_count} PASS{carry_note}</span>
      </div>
      <p class="kpi"><b>Deciding metric:</b> {escape(ind["kpi"])}</p>
      <p class="note">{escape(ind["note"])}</p>
      <div class="twrap"><table>
        <thead><tr>
          <th>Company</th><th class="num">Price</th><th class="num">Mkt Cap</th><th class="num">ROCE</th>
          <th class="num">ROE</th><th class="num">Sales 5y</th><th class="num">PAT 5y</th>
          <th class="num">OPM</th><th class="num">D/E</th><th class="num">P/E</th><th class="num">Score</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
    </section>"""


def render(data):
    groups = {}
    for ind in data["industries"]:
        groups.setdefault(ind["group"], []).append(ind)

    sections = ""
    for group, inds in groups.items():
        cards = "".join(render_industry(i) for i in inds)
        sections += f'<div class="group"><h2>{escape(group)}</h2>{cards}</div>'

    companies = [c for ind in data["industries"] for c in ind["top3"]]
    pass_count = sum(1 for c in companies if c.get("passed"))
    carry_count = sum(1 for c in companies if c.get("data_status") == "carried_forward")
    fresh_count = data.get("fresh_top_count", data.get("fresh_count", len(companies) - carry_count))
    total_candidates = sum(i["candidates_total"] for i in data["industries"])
    fetched_candidates = sum(i["candidates_fetched"] for i in data["industries"])
    leaders = sorted((c for c in companies if c.get("passed")), key=lambda x: x.get("score", 0), reverse=True)[:8]
    leader_html = "".join(
        f'<li><a href="https://www.screener.in/company/{quote(c["ticker"], safe="")}/consolidated/" target="_blank" rel="noopener"><b>{escape(c["ticker"])}</b></a> '
        f'{escape(c.get("name") or "")} <span>{fmt(c.get("score"))}</span></li>'
        for c in leaders
    ) or "<li>No current PASS rows in this snapshot.</li>"
    bf = data["base_filter"]
    data_status = "Healthy" if data.get("failed_count", 0) == 0 else "Partial refresh"
    status_detail = (
        f'{data_status}: {fresh_count} fresh rows'
        + (f', {carry_count} carried forward' if carry_count else "")
        + (f', {data.get("failed_count")} fetch failures' if data.get("failed_count") else "")
    )

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>India Industry Screener — Daily Fundamental Screen</title>
<meta name="description" content="Daily educational quantitative screen of Indian listed industries with transparent coverage, quality filters and source links. Not investment advice.">
<style>
  :root { --bg:#f5f7fb; --card:#fff; --ink:#101828; --muted:#667085; --line:#e4e7ec; --accent:#175cd3; --ok:#067647; --weak:#b42318; --flag:#b54708; --chip:#eef4ff; --shadow:0 8px 24px rgba(16,24,40,.06); }
  @media (prefers-color-scheme: dark) { :root { --bg:#0b1220; --card:#111a2b; --ink:#f2f4f7; --muted:#98a2b3; --line:#27344a; --accent:#84adff; --ok:#6ce9a6; --weak:#f97066; --flag:#fdb022; --chip:#1d2939; --shadow:none; } }
  :root[data-theme="dark"] { --bg:#0b1220; --card:#111a2b; --ink:#f2f4f7; --muted:#98a2b3; --line:#27344a; --accent:#84adff; --ok:#6ce9a6; --weak:#f97066; --flag:#fdb022; --chip:#1d2939; --shadow:none; }
  :root[data-theme="light"] { --bg:#f5f7fb; --card:#fff; --ink:#101828; --muted:#667085; --line:#e4e7ec; --accent:#175cd3; --ok:#067647; --weak:#b42318; --flag:#b54708; --chip:#eef4ff; --shadow:0 8px 24px rgba(16,24,40,.06); }
  * { box-sizing:border-box; } body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; }
  .wrap { max-width:1180px; margin:0 auto; padding:28px 18px 80px; } header { padding-right:70px; } header h1 { font-size:2rem; margin:0 0 4px; letter-spacing:-.03em; } .sub { color:var(--muted); margin:0 0 4px; } .stamp { color:var(--muted); font-size:.84rem; }
  .status { display:flex; gap:8px; flex-wrap:wrap; margin:18px 0 14px; } .status-card { flex:1 1 150px; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 14px; box-shadow:var(--shadow); } .status-card b { display:block; font-size:1.3rem; } .status-card span { color:var(--muted); font-size:.78rem; }
  .banner { background:var(--card); border:1px solid var(--line); border-left:4px solid var(--flag); border-radius:10px; padding:13px 15px; margin:14px 0; font-size:.88rem; color:var(--muted); } .banner b { color:var(--ink); }
  .controls { display:flex; gap:8px; flex-wrap:wrap; align-items:center; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px; margin:14px 0 24px; position:sticky; top:0; z-index:2; box-shadow:var(--shadow); } input, select, button { font:inherit; border:1px solid var(--line); border-radius:8px; background:var(--card); color:var(--ink); padding:8px 10px; } input { flex:1 1 240px; } button { cursor:pointer; } .hint { color:var(--muted); font-size:.78rem; margin-left:auto; }
  .method { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:13px 15px; margin:0 0 24px; font-size:.88rem; } .method summary { cursor:pointer; font-weight:650; } .method ul { margin:10px 0 0; padding-left:18px; color:var(--muted); }
  .group > h2 { font-size:1.12rem; margin:30px 0 8px; padding-bottom:6px; border-bottom:2px solid var(--line); } .ind { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; margin:13px 0; box-shadow:var(--shadow); } .ind.hidden { display:none; }
  .ind-head { display:flex; align-items:baseline; justify-content:space-between; gap:10px; flex-wrap:wrap; } .ind h3 { margin:0; font-size:1.04rem; } .cov { color:var(--muted); font-size:.78rem; white-space:nowrap; } .kind { font-size:.63rem; text-transform:uppercase; letter-spacing:.04em; padding:2px 7px; border-radius:20px; background:var(--chip); color:var(--muted); vertical-align:middle; margin-left:6px; } .kind.cyclical { color:var(--weak); } .kind.financial { color:var(--accent); } .kind.realestate { color:var(--flag); }
  .kpi { margin:8px 0 2px; font-size:.84rem; color:var(--muted); } .kpi b { color:var(--ink); } .note { margin:2px 0 10px; font-size:.81rem; color:var(--muted); font-style:italic; } .twrap { overflow-x:auto; } table { width:100%; border-collapse:collapse; font-size:.81rem; min-width:860px; } th, td { padding:8px 8px; text-align:left; border-bottom:1px solid var(--line); } th.num, td.num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; } thead th { color:var(--muted); font-weight:650; font-size:.74rem; } td.num.ok { color:var(--ok); } td.num.weak { color:var(--weak); } .tk .sym { font-weight:750; color:var(--accent); text-decoration:none; } .cname { color:var(--muted); font-size:.73rem; margin-top:2px; } .fails { color:var(--flag); font-size:.7rem; margin-top:2px; } .score { font-weight:700; } .badge { font-size:.59rem; text-transform:uppercase; letter-spacing:.03em; padding:2px 5px; border-radius:20px; margin-left:5px; vertical-align:middle; white-space:nowrap; } .badge.pass, .badge.fresh { background:color-mix(in srgb,var(--ok) 16%,transparent); color:var(--ok); } .badge.flag, .badge.carry { background:color-mix(in srgb,var(--flag) 16%,transparent); color:var(--flag); } .empty { color:var(--muted); text-align:center; font-style:italic; }
  .lower { display:grid; grid-template-columns:1.1fr .9fr; gap:14px; margin-top:24px; } .panel { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:15px; } .panel h2 { font-size:1rem; margin:0 0 8px; } .panel p { color:var(--muted); font-size:.82rem; margin:0 0 8px; } .leaders { margin:0; padding-left:19px; color:var(--muted); font-size:.82rem; } .leaders li { margin:5px 0; } .leaders b { color:var(--ink); } .leaders span { float:right; color:var(--accent); font-variant-numeric:tabular-nums; }
  .toggle { position:fixed; top:14px; right:14px; background:var(--card); border:1px solid var(--line); color:var(--ink); border-radius:20px; padding:6px 12px; font-size:.78rem; cursor:pointer; z-index:3; } footer { margin-top:34px; color:var(--muted); font-size:.78rem; text-align:center; } a { color:var(--accent); }
  @media (max-width:720px) { .wrap { padding:22px 12px 60px; } header h1 { font-size:1.65rem; } .lower { grid-template-columns:1fr; } .hint { width:100%; margin-left:0; } }
</style>
</head>
<body>
<button class="toggle" onclick="tt()">◐ theme</button>
<div class="wrap">
  <header>
    <h1>India Industry Screener</h1>
    <p class="sub">Daily, transparent quality screen across Indian industries · source-linked company rows · no price targets or buy/sell calls</p>
    <p class="stamp">Last refreshed: <b>""" + escape(data["generated_at"]) + """</b> · """ + str(data["industry_count"]) + """ industries · planned daily refresh around 08:00 IST</p>
  </header>

  <div class="status">
    <div class="status-card"><b>""" + str(fetched_candidates) + "/" + str(total_candidates) + """</b><span>candidate coverage</span></div>
    <div class="status-card"><b>""" + str(pass_count) + """</b><span>PASS rows in top 3</span></div>
    <div class="status-card"><b>""" + str(fresh_count) + """</b><span>fresh top rows</span></div>
    <div class="status-card"><b>""" + str(data.get("failed_count", 0)) + """</b><span>fetch failures</span></div>
  </div>

  <div class="banner">
    <b>Data status: """ + escape(status_detail) + """</b>. Metrics are trailing reported figures from
    <a href="https://www.screener.in/" target="_blank" rel="noopener">screener.in</a>.
    Carried-forward rows are explicitly labelled; verify source pages before using any figure.
  </div>

  <div class="banner">
    <b>Educational tool — not investment advice.</b> This automated screen is for information and
    education only. It is not a recommendation, solicitation, or advice to buy, sell, or hold any
    security. The author is not a SEBI-registered Research Analyst or Investment Adviser. Rankings
    may contain data errors. Do your own research and consult a SEBI-registered adviser.
  </div>

  <details class="method">
    <summary>Method, filters and data limitations</summary>
    <ul>
      <li><b>Base quality filter:</b> ROCE ≥ """ + str(bf["roce_min"]) + """%, ROE ≥ """ + str(bf["roe_min"]) + """%, 5-year sales CAGR ≥ """ + str(bf["sales_cagr_min"]) + """%, 5-year profit CAGR ≥ """ + str(bf["profit_cagr_min"]) + """%, D/E ≤ """ + str(bf["de_max"]) + """. PASS means all applicable thresholds are met.</li>
      <li><b>Financials</b> use ROE and growth because ROCE, OPM and D/E are not comparable for lenders. Review ROA, NIM, GNPA/NNPA, CASA, CAR, VNB and combined ratio separately.</li>
      <li><b>Cyclicals and real estate</b> are shown for relative context; trailing returns can be structurally misleading at different points in the cycle.</li>
      <li>Rows link to the consolidated company page on screener.in. The screen does not scrape sector KPIs, news, management quality, valuations beyond P/E, or forward estimates.</li>
      <li>Daily scheduling is best-effort: GitHub Actions can delay scheduled jobs. The timestamp and fetch status above are the source of truth.</li>
    </ul>
  </details>

  <div class="controls">
    <input id="search" type="search" placeholder="Search company or ticker…" aria-label="Search company or ticker">
    <select id="kind"><option value="">All industry types</option><option value="general">General</option><option value="financial">Financial</option><option value="cyclical">Cyclical</option><option value="realestate">Real estate</option></select>
    <select id="quality"><option value="">All quality states</option><option value="pass">PASS only</option><option value="flag">Flagged only</option><option value="carry">Carried-forward rows</option></select>
    <button onclick="resetFilters()">Reset</button><span class="hint" id="count"></span>
  </div>

  <div id="sections">""" + sections + """</div>

  <div class="lower">
    <section class="panel"><h2>Highest-scoring PASS rows</h2><p>Mechanical screen leaders only; score is not a forecast or recommendation.</p><ol class="leaders">""" + leader_html + """</ol></section>
    <section class="panel"><h2>Refresh contract</h2><p>Source: screener.in company pages. Current run: """ + escape(data.get("source_status", "unknown")) + """.</p><p>Latest fetch failures are not silently replaced: prior successful rows are carried forward and labelled, while missing names remain visible through coverage counts.</p></section>
  </div>

  <footer>Generated by the open-source screening pipeline · verify all figures independently · data © screener.in</footer>
</div>
<script>
  function tt(){var r=document.documentElement;var d=r.getAttribute('data-theme');var cur=d||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');r.setAttribute('data-theme',cur==='dark'?'light':'dark');}
  function applyFilters(){var q=(document.getElementById('search').value||'').toLowerCase().trim(), k=document.getElementById('kind').value, quality=document.getElementById('quality').value, visible=0, total=0;
    document.querySelectorAll('.ind').forEach(function(ind){var kindOk=!k||ind.dataset.kind===k, rows=ind.querySelectorAll('.company-row'), indVisible=0;
      rows.forEach(function(row){var searchOk=!q||row.dataset.search.toLowerCase().includes(q), status=row.dataset.status, pass=row.querySelector('.badge.pass'), qualityOk=!quality||(quality==='pass'&&pass)||(quality==='flag'&&!pass&&status!=='carried_forward')||(quality==='carry'&&status==='carried_forward'); var show=kindOk&&searchOk&&qualityOk; row.style.display=show?'':'none'; if(show){indVisible++;visible++;} total++;});
      ind.classList.toggle('hidden',indVisible===0);
    }); document.getElementById('count').textContent=visible+' visible rows · '+total+' total rows';}
  function resetFilters(){document.getElementById('search').value='';document.getElementById('kind').value='';document.getElementById('quality').value='';applyFilters();}
  document.getElementById('search').addEventListener('input',applyFilters);document.getElementById('kind').addEventListener('change',applyFilters);document.getElementById('quality').addEventListener('change',applyFilters);applyFilters();
</script>
</body>
</html>"""


def main():
    with open(DATA) as f:
        data = json.load(f)
    with open(OUT, "w") as f:
        f.write(render(data))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
