"""
Industry universe + per-industry screening configuration.

Each industry has:
  - kind:  'general' | 'financial' | 'cyclical' | 'realestate'
           drives which base filter is applied and how names are ranked.
  - kpi:   the sector-specific "deciding metric" (shown on the site as an
           analyst note; NOT auto-scraped from screener.in standard pages).
  - note:  short caveat shown under the industry.
  - tickers: candidate universe (screener.in / NSE symbols). The screen ranks
           the top 3 from whichever of these it can fetch.

The automated bi-weekly engine ranks on the fundamental-quality metrics that
screener.in reliably exposes on a company page: ROCE, ROE, 5yr sales CAGR,
5yr profit CAGR, OPM and Debt/Equity. Sector-specific KPIs (ROA, NIM, GNPA,
combined ratio, ARPOB, EBITDA/tonne, pre-sales, order book) are captured as
static analyst context, not scraped.
"""

BASE_FILTER = {
    "roce_min": 15.0,
    "roe_min": 15.0,
    "sales_cagr_min": 10.0,
    "profit_cagr_min": 12.0,
    "de_max": 1.0,
}

INDUSTRIES = [
    # ---------------- FINANCIALS ----------------
    {
        "name": "Private Banks", "group": "Financials", "kind": "financial",
        "kpi": "ROA >1.5%, NIM, GNPA/NNPA, CASA, CAR (not scraped — manual review)",
        "note": "Banks ranked on ROE + profit growth; ROCE/OPM/D-E are not meaningful for lenders.",
        "tickers": ["ICICIBANK", "HDFCBANK", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "IDFCFIRSTB", "FEDERALBNK"],
    },
    {
        "name": "PSU Banks", "group": "Financials", "kind": "financial",
        "kpi": "ROA >0.9%, GNPA/NNPA, CASA, CAR, P/B (not scraped)",
        "note": "Ranked on ROE + profit growth. Verify asset-quality on screener.in before use.",
        "tickers": ["SBIN", "BANKBARODA", "INDIANB", "PNB", "CANBK", "UNIONBANK"],
    },
    {
        "name": "NBFCs", "group": "Financials", "kind": "financial",
        "kpi": "ROA, NIM/spread, GNPA/NNPA, cost-to-income, CAR, AUM growth (not scraped)",
        "note": "Ranked on ROE + profit growth.",
        "tickers": ["BAJFINANCE", "CHOLAFIN", "SHRIRAMFIN", "SUNDARMFIN", "MUTHOOTFIN", "MANAPPURAM", "LTF"],
    },
    {
        "name": "Housing Finance", "group": "Financials", "kind": "financial",
        "kpi": "ROA, spread, GNPA/NNPA, CAR, AUM growth (not scraped)",
        "note": "Ranked on ROE + profit growth.",
        "tickers": ["BAJAJHFL", "AAVAS", "HOMEFIRST", "CANFINHOME", "APTUS", "LICHSGFIN", "PNBHOUSING"],
    },
    {
        "name": "Life Insurance", "group": "Financials", "kind": "financial",
        "kpi": "VNB margin, APE growth, persistency, RoEV (not scraped)",
        "note": "Screener metrics are weak proxies for insurers — treat ranking as indicative only.",
        "tickers": ["HDFCLIFE", "SBILIFE", "ICICIPRULI", "MFSL", "LICI"],
    },
    {
        "name": "General & Health Insurance", "group": "Financials", "kind": "financial",
        "kpi": "Combined ratio <100%, solvency, loss ratio, GWP growth (not scraped)",
        "note": "Screener metrics are weak proxies for insurers — indicative only.",
        "tickers": ["ICICIGI", "STARHEALTH", "GODIGIT", "NIVABUPA", "NIACL"],
    },
    {
        "name": "Capital Markets & AMCs", "group": "Financials", "kind": "general",
        "kpi": "ROE >25%, debt-free, AUM/volume growth, operating margin",
        "note": "Asset-light — the general quality filter works well here.",
        "tickers": ["BSE", "CDSL", "HDFCAMC", "MCX", "CAMS", "NAM-INDIA", "360ONE", "ANGELONE", "KFINTECH"],
    },
    # ---------------- TECH / CONSUMER / HEALTH ----------------
    {
        "name": "IT / Software Services", "group": "Tech & Consumer", "kind": "general",
        "kpi": "Constant-currency growth, EBIT margin >20%, attrition, deal TCV, FCF conversion",
        "note": "Mega-caps often miss the 12% profit-CAGR bar; mid-caps score on growth.",
        "tickers": ["TCS", "INFY", "HCLTECH", "WIPRO", "LTIM", "PERSISTENT", "COFORGE", "HEXT", "MPHASIS"],
    },
    {
        "name": "FMCG", "group": "Tech & Consumer", "kind": "general",
        "kpi": "Volume growth, OPM >18%, ROCE >25%, cash conversion",
        "note": "Sector-wide growth is soft; several elite-return names miss the growth filter.",
        "tickers": ["HINDUNILVR", "NESTLEIND", "VBL", "BRITANNIA", "MARICO", "DABUR", "COLPAL", "TATACONSUM", "GODREJCP"],
    },
    {
        "name": "Pharma", "group": "Tech & Consumer", "kind": "general",
        "kpi": "OPM >18%, D/E <0.5, USFDA status, R&D pipeline",
        "note": "Check USFDA inspection status separately — not on screener.",
        "tickers": ["SUNPHARMA", "DIVISLAB", "CIPLA", "DRREDDY", "AJANTPHARM", "TORNTPHARM", "MANKIND", "LUPIN", "ALKEM"],
    },
    {
        "name": "Hospitals & Diagnostics", "group": "Tech & Consumer", "kind": "general",
        "kpi": "ARPOB, occupancy, bed additions (hospitals); ROCE, network (diagnostics)",
        "note": "Expansion capex can depress trailing ROCE for the fastest growers.",
        "tickers": ["APOLLOHOSP", "MAXHEALTH", "FORTIS", "NH", "LALPATHLAB", "METROPOLIS", "VIJAYA"],
    },
    # ---------------- AUTO / METALS / CEMENT ----------------
    {
        "name": "Auto OEMs", "group": "Auto, Metals & Cement", "kind": "general",
        "kpi": "Volume growth, market-share trend, EBITDA margin, EV readiness",
        "note": "Captive-finance arms distort consolidated ROCE/D-E for some OEMs.",
        "tickers": ["MARUTI", "M&M", "TATAMOTORS", "EICHERMOT", "BAJAJ-AUTO", "HEROMOTOCO", "TVSMOTOR", "ASHOKLEY"],
    },
    {
        "name": "Auto Ancillaries", "group": "Auto, Metals & Cement", "kind": "general",
        "kpi": "Content per vehicle, client diversification, export %, ROCE",
        "note": "Export % not on screener — verify separately.",
        "tickers": ["BOSCHLTD", "SCHAEFFLER", "UNOMINDA", "MOTHERSON", "BALKRISIND", "ENDURANCE", "SUNDRMFAST", "TIINDIA"],
    },
    {
        "name": "Metals & Mining", "group": "Auto, Metals & Cement", "kind": "cyclical",
        "kpi": "EV/EBITDA, cost-per-tonne, net-debt/EBITDA <3, capacity utilisation",
        "note": "Cyclical — trailing returns near cycle peak; ranked on relative strength + balance sheet.",
        "tickers": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "HINDZINC", "VEDL", "NMDC", "JINDALSTEL", "JSL", "SAIL"],
    },
    {
        "name": "Cement", "group": "Auto, Metals & Cement", "kind": "cyclical",
        "kpi": "EBITDA/tonne, capacity utilisation >70%, realisations, regional strength",
        "note": "Cyclical — fresh off a pricing trough; few names pass the full filter.",
        "tickers": ["ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "DALBHARAT", "JKCEMENT", "RAMCOCEM"],
    },
    # ---------------- INDUSTRIALS / ENERGY ----------------
    {
        "name": "Capital Goods & Engineering", "group": "Industrials & Energy", "kind": "general",
        "kpi": "Order book & book-to-bill >2.5x, order inflow, execution, working capital",
        "note": "Order book not on screener — verify from company disclosures.",
        "tickers": ["LT", "SIEMENS", "ABB", "CUMMINSIND", "TRITURBINE", "THERMAX", "BHEL"],
    },
    {
        "name": "Defence", "group": "Industrials & Energy", "kind": "general",
        "kpi": "Order book & book-to-bill, indigenisation %, order inflow",
        "note": "Multi-year order visibility not captured by screener ratios.",
        "tickers": ["HAL", "BEL", "BDL", "MAZDOCK", "SOLARINDS", "DATAPATTNS", "COCHINSHIP"],
    },
    {
        "name": "Power & Utilities", "group": "Industrials & Energy", "kind": "cyclical",
        "kpi": "PLF/capacity utilisation, regulated vs merchant, receivable days, RE pipeline",
        "note": "Regulated-return model structurally caps ROCE — most names fail the filter (not a defect).",
        "tickers": ["NTPC", "POWERGRID", "TATAPOWER", "ADANIPOWER", "JSWENERGY", "TORNTPOWER", "NHPC"],
    },
    {
        "name": "Oil & Gas / Energy", "group": "Industrials & Energy", "kind": "cyclical",
        "kpi": "GRM (OMCs), crude leverage (upstream), volume growth & margin/scm (CGD)",
        "note": "Commodity/regulated — upstream & CGD often sit at 12-14% ROE.",
        "tickers": ["RELIANCE", "ONGC", "IOC", "BPCL", "GAIL", "PETRONET", "IGL", "MGL", "OIL", "CASTROLIND"],
    },
    # ---------------- OTHER ----------------
    {
        "name": "Building Materials", "group": "Other Sectors", "kind": "general",
        "kpi": "Brand strength, OPM, ROCE >18%, distribution, volume growth",
        "note": "Construction soft patch has softened trailing ratios for some names.",
        "tickers": ["APLAPOLLO", "KAJARIACER", "ASTRAL", "SUPREMEIND", "CERA", "PIDILITIND", "ASIANPAINT", "BERGEPAINT"],
    },
    {
        "name": "Telecom", "group": "Other Sectors", "kind": "general",
        "kpi": "ARPU & trend, subscriber/market share, net debt, EBITDA margin",
        "note": "Carriers carry heavy absolute debt; tower/infra layer scores cleanest.",
        "tickers": ["BHARTIARTL", "INDUSTOWER", "TATACOMM", "HFCL", "BHARTIHEXA"],
    },
    {
        "name": "Media & Entertainment", "group": "Other Sectors", "kind": "general",
        "kpi": "FCF, balance sheet, content/IP ownership (be selective)",
        "note": "Most of the sector destroys capital; winners are debt-free IP owners.",
        "tickers": ["SUNTV", "TIPSMUSIC", "SAREGAMA", "ZEEL", "PVRINOX", "NAZARA"],
    },
    {
        "name": "Logistics & Ports", "group": "Other Sectors", "kind": "general",
        "kpi": "Throughput growth, asset turns, EBITDA/unit, network density",
        "note": "Ports are high-margin; surface transport is asset-turn driven.",
        "tickers": ["ADANIPORTS", "JSWINFRA", "CONCOR", "TCI", "DELHIVERY", "BLUEDART", "GATI"],
    },
    {
        "name": "Hotels & Tourism", "group": "Other Sectors", "kind": "cyclical",
        "kpi": "RevPAR, occupancy, ARR, room additions",
        "note": "Mid/late upcycle; asset-heavy base depresses ROE — prefer low-debt owners.",
        "tickers": ["INDHOTEL", "EIHOTEL", "CHALET", "LEMONTREE", "ITCHOTELS"],
    },
    {
        "name": "Aviation", "group": "Other Sectors", "kind": "cyclical",
        "kpi": "Load factor, RASK/CASK spread, fleet, balance sheet (usually weak)",
        "note": "Only one structurally profitable listed carrier — be honest about thin depth.",
        "tickers": ["INDIGO", "SPICEJET"],
    },
    {
        "name": "Textiles", "group": "Other Sectors", "kind": "cyclical",
        "kpi": "Cost position, capacity utilisation, debt, export/value-add mix",
        "note": "Favour low-cost, high-value-add, debt-light exporters over commodity spinners.",
        "tickers": ["PAGEIND", "KPRMILL", "GARFIBRES", "TRIDENT", "WELSPUNLIV", "VARDHACRLC", "RAYMOND"],
    },
    {
        "name": "Real Estate", "group": "Other Sectors", "kind": "realestate",
        "kpi": "Pre-sales/bookings growth (lead), net debt, collections — use NAV not P/E",
        "note": "Revenue-recognition lag makes ROCE/ROE fail by design — that is normal here.",
        "tickers": ["DLF", "GODREJPROP", "LODHA", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD", "BRIGADE"],
    },
    {
        "name": "Consumer Durables & Electricals", "group": "Other Sectors", "kind": "general",
        "kpi": "Volume growth, premiumisation, OPM, working capital, ROCE",
        "note": "Cables/wires and cooling names lead on returns + growth.",
        "tickers": ["POLYCAB", "HAVELLS", "BLUESTARCO", "KEI", "VOLTAS", "CROMPTON", "WHIRLPOOL", "VGUARD"],
    },
    {
        "name": "Electronics Manufacturing (EMS)", "group": "Other Sectors", "kind": "general",
        "kpi": "Order book, client wins, revenue growth, asset turns, ROCE (thin margins are structural)",
        "note": "Judge on ROCE + asset turns + growth, not margin.",
        "tickers": ["DIXON", "KAYNES", "SYRMA", "AMBER", "CYIENTDLM", "AVALON"],
    },
    {
        "name": "Specialty Chemicals", "group": "Other Sectors", "kind": "general",
        "kpi": "ROCE >18%, OPM >18%, R&D, China+1 wins, capex runway, asset turns",
        "note": "FY23-26 down-cycle depresses trailing growth for several quality names.",
        "tickers": ["NAVINFLUOR", "VINATIORGA", "CLEAN", "PIIND", "DEEPAKNTR", "AARTIIND", "SRF", "ATUL", "FLUOROCHEM"],
    },
]

if __name__ == "__main__":
    total = sum(len(i["tickers"]) for i in INDUSTRIES)
    print(f"{len(INDUSTRIES)} industries, {total} candidate tickers")
