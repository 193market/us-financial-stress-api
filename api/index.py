from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from datetime import datetime

app = FastAPI(
    title="US Financial Stress API",
    description="US financial market stress indicators including the St. Louis Fed Financial Stress Index, VIX volatility, credit spreads, yield curve, and market risk metrics. Powered by FRED.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

SERIES = {
    "fsi":              {"id": "STLFSI4",      "name": "St. Louis Fed Financial Stress Index",   "unit": "Index",           "frequency": "Weekly"},
    "vix":              {"id": "VIXCLS",       "name": "CBOE Volatility Index (VIX)",            "unit": "Index",           "frequency": "Daily"},
    "yield_curve":      {"id": "T10Y2Y",       "name": "10Y-2Y Treasury Yield Spread",           "unit": "Percentage Points","frequency": "Daily"},
    "ted_spread":       {"id": "TEDRATE",      "name": "TED Spread",                             "unit": "Percentage Points","frequency": "Daily"},
    "credit_spread_hy": {"id": "BAMLH0A0HYM2", "name": "High Yield Credit Spread",              "unit": "Percentage Points","frequency": "Daily"},
    "credit_spread_ig": {"id": "BAMLC0A0CM",   "name": "Investment Grade Credit Spread",         "unit": "Percentage Points","frequency": "Daily"},
    "libor_ois":        {"id": "LLOIRAM3M156N", "name": "LIBOR-OIS Spread (3M)",                 "unit": "Percentage Points","frequency": "Monthly"},
    "nfci":             {"id": "NFCI",          "name": "Chicago Fed National Financial Conditions Index","unit": "Index",    "frequency": "Weekly"},
    "treasury_10y":     {"id": "GS10",          "name": "10-Year Treasury Yield",                "unit": "%",               "frequency": "Monthly"},
    "fed_funds":        {"id": "FEDFUNDS",      "name": "Federal Funds Rate",                    "unit": "%",               "frequency": "Monthly"},
}


async def fetch_fred(series_id: str, limit: int = 52):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.get(FRED_BASE, params=params)
        data = res.json()
    obs = data.get("observations", [])
    return [
        {"date": o["date"], "value": float(o["value"]) if o["value"] != "." else None}
        for o in obs
        if o.get("value") != "."
    ]


@app.get("/")
def root():
    return {
        "api": "US Financial Stress API",
        "version": "1.0.0",
        "provider": "GlobalData Store",
        "source": "FRED - Federal Reserve Bank of St. Louis",
        "endpoints": ["/summary", "/stress-index", "/vix", "/yield-curve", "/credit-spreads", "/ted-spread", "/nfci", "/treasury", "/fed-funds"],
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/summary")
async def summary(limit: int = Query(default=52, ge=1, le=260)):
    """All financial stress indicators snapshot"""
    results = {}
    for key, meta in SERIES.items():
        results[key] = await fetch_fred(meta["id"], limit)
    formatted = {
        key: {
            "name": SERIES[key]["name"],
            "unit": SERIES[key]["unit"],
            "frequency": SERIES[key]["frequency"],
            "data": results[key],
        }
        for key in SERIES
    }
    return {
        "country": "United States",
        "source": "FRED - Federal Reserve Bank of St. Louis",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "indicators": formatted,
    }


@app.get("/stress-index")
async def stress_index(limit: int = Query(default=104, ge=1, le=520)):
    """St. Louis Fed Financial Stress Index (weekly; values above 0 = above-average stress)"""
    data = await fetch_fred("STLFSI4", limit)
    return {"indicator": "St. Louis Fed Financial Stress Index", "series_id": "STLFSI4", "unit": "Index (0=average)", "frequency": "Weekly", "note": "Values above 0 indicate above-average financial stress", "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z", "data": data}


@app.get("/vix")
async def vix(limit: int = Query(default=252, ge=1, le=1260)):
    """CBOE Volatility Index (VIX) — fear gauge of S&P 500 options"""
    data = await fetch_fred("VIXCLS", limit)
    return {"indicator": "CBOE VIX Volatility Index", "series_id": "VIXCLS", "unit": "Index", "frequency": "Daily", "note": "Values above 20 indicate elevated market uncertainty", "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z", "data": data}


@app.get("/yield-curve")
async def yield_curve(limit: int = Query(default=252, ge=1, le=1260)):
    """10Y-2Y Treasury yield spread (inversion signals recession risk)"""
    data = await fetch_fred("T10Y2Y", limit)
    return {"indicator": "10Y-2Y Treasury Yield Spread", "series_id": "T10Y2Y", "unit": "Percentage Points", "frequency": "Daily", "note": "Negative values = inverted yield curve (recession signal)", "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z", "data": data}


@app.get("/credit-spreads")
async def credit_spreads(limit: int = Query(default=252, ge=1, le=1260)):
    """High yield and investment grade credit spreads"""
    hy = await fetch_fred("BAMLH0A0HYM2", limit)
    ig = await fetch_fred("BAMLC0A0CM", limit)
    return {
        "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z",
        "high_yield": {"series_id": "BAMLH0A0HYM2", "name": "High Yield Credit Spread", "unit": "Percentage Points", "frequency": "Daily", "data": hy},
        "investment_grade": {"series_id": "BAMLC0A0CM", "name": "Investment Grade Credit Spread", "unit": "Percentage Points", "frequency": "Daily", "data": ig},
    }


@app.get("/ted-spread")
async def ted_spread(limit: int = Query(default=252, ge=1, le=1260)):
    """TED spread — difference between 3-month LIBOR and T-bill rate"""
    data = await fetch_fred("TEDRATE", limit)
    return {"indicator": "TED Spread", "series_id": "TEDRATE", "unit": "Percentage Points", "frequency": "Daily", "note": "Higher = more credit stress in banking system", "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z", "data": data}


@app.get("/nfci")
async def nfci(limit: int = Query(default=104, ge=1, le=520)):
    """Chicago Fed National Financial Conditions Index"""
    data = await fetch_fred("NFCI", limit)
    return {"indicator": "Chicago Fed National Financial Conditions Index", "series_id": "NFCI", "unit": "Index (0=average)", "frequency": "Weekly", "note": "Negative = looser than average; Positive = tighter than average", "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z", "data": data}


@app.get("/treasury")
async def treasury(limit: int = Query(default=60, ge=1, le=360)):
    """10-Year Treasury yield (%)"""
    data = await fetch_fred("GS10", limit)
    return {"indicator": "10-Year Treasury Yield", "series_id": "GS10", "unit": "%", "frequency": "Monthly", "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z", "data": data}


@app.get("/fed-funds")
async def fed_funds(limit: int = Query(default=60, ge=1, le=360)):
    """Effective Federal Funds Rate (%)"""
    data = await fetch_fred("FEDFUNDS", limit)
    return {"indicator": "Federal Funds Rate", "series_id": "FEDFUNDS", "unit": "%", "frequency": "Monthly", "source": "FRED", "updated_at": datetime.utcnow().isoformat() + "Z", "data": data}
