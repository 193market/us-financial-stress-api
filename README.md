# US Financial Stress API

US financial market stress indicators including the St. Louis Fed Financial Stress Index, VIX volatility index, yield curve (10Y-2Y spread), credit spreads, TED spread, and Chicago Fed National Financial Conditions Index. Powered by FRED.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API info and available endpoints |
| `GET /summary` | All financial stress indicators snapshot |
| `GET /stress-index` | St. Louis Fed Financial Stress Index |
| `GET /vix` | CBOE VIX Volatility Index |
| `GET /yield-curve` | 10Y-2Y Treasury Yield Spread |
| `GET /credit-spreads` | High yield & investment grade spreads |
| `GET /ted-spread` | TED Spread (LIBOR-Treasury) |
| `GET /nfci` | Chicago Fed Financial Conditions Index |
| `GET /treasury` | 10-Year Treasury yield |
| `GET /fed-funds` | Federal Funds Rate |

## Data Source

FRED — Federal Reserve Bank of St. Louis
https://fred.stlouisfed.org

## Authentication

Requires `X-RapidAPI-Key` header via RapidAPI.
