# Finance Companion

**A full-stack stock research app: search companies, follow live quotes and price history, keep a watchlist, and build side-by-side performance reports.**

[![CI](https://github.com/Simos98/Stock-Tracker-App/actions/workflows/ci.yml/badge.svg)](https://github.com/Simos98/Stock-Tracker-App/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![React](https://img.shields.io/badge/react-18-61dafb)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

<!-- Replace with a real screenshot or GIF: save it as docs/screenshot.png and uncomment the next line. -->
<!-- ![Finance Companion dashboard](docs/screenshot.png) -->

> **Screenshot coming soon:** dashboard, stock detail and report builder.

## The problem

Retail investors who follow a handful of companies end up juggling broker apps, news sites and spreadsheets to answer simple questions:

- How has this stock moved this month?
- How does it compare with the others I'm watching?

Finance Companion puts search, quotes, history, a personal watchlist and quick comparison reports behind one login. The UI is aimed at the Australian market.

## Features

- **Stock search** over a local catalogue, falling back to Alpha Vantage's symbol search and caching what it finds
- **Stock detail pages** with the latest quote and daily, weekly or monthly price history
- **Personal watchlist** with on-demand price refresh
- **Report builder:** compare up to 5 stocks over 1 week to 5 years (latest close, high/low, average volume, % change)
- **Accounts:** sign-up, login, profile and password changes, notification preferences
- **Secure sessions:** short-lived access tokens, silent refresh and real server-side logout

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | React 18, React Router 7, Axios, Vite |
| Backend | Python, Flask 3, Flask-JWT-Extended, Flask-SQLAlchemy (SQLAlchemy 2), Flask-CORS |
| Data | SQLite by default; MySQL via `DATABASE_URL` |
| Market data | [Alpha Vantage](https://www.alphavantage.co/) REST API |
| Quality | pytest, Ruff, ESLint, Prettier, GitHub Actions |

## Getting started

**Prerequisites:**
- Python 3.12+
- Node.js 20+
- A free [Alpha Vantage API key](https://www.alphavantage.co/support/#api-key)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env               # Windows: copy .env.example .env
# then set ALPHAVANTAGE_API_KEY in backend/.env

flask --app src.main seed-stocks   # optional: adds 10 large ASX companies
python -m src.main                 # API on http://127.0.0.1:5000
```

The app uses a SQLite file in `backend/instance/` unless you set `DATABASE_URL`. For MySQL, use for example `mysql+pymysql://user:password@localhost:3306/finance_companion`. Tables are created on startup.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev                        # http://localhost:5173
```

The Vite dev server proxies `/api` to Flask, so there's no CORS setup to do. If Flask runs on another port, set `API_PROXY_TARGET` (for example `http://127.0.0.1:5001`). On macOS, AirPlay Receiver occupies port 5000 by default.

### Single-server mode

`npm run build` writes the production bundle to `backend/src/static/`. Flask then serves the whole app at `http://127.0.0.1:5000`, including client-side routes.

### Tests and checks

```bash
# in backend/
pytest
ruff check . && ruff format --check .

# in frontend/
npm run lint && npm run format:check && npm run build
```

The same checks run in CI on every push and pull request.

## Project structure

```text
Stock-Tracker-App/
├── backend/
│   ├── src/
│   │   ├── __init__.py          # create_app(): config, extensions, blueprints, error handlers, SPA fallback
│   │   ├── config.py            # settings from environment variables, fail-fast secrets
│   │   ├── models.py            # User, Stock, UserWatchlist, UserPreference, SavedStockData
│   │   ├── cli.py               # `flask seed-stocks`
│   │   ├── routes/              # one blueprint per resource under /api/v1
│   │   ├── services/
│   │   │   └── alpha_vantage.py # market-data client: errors, caching, throttling
│   │   └── main.py              # entry point (`python -m src.main`)
│   └── tests/                   # pytest suite (in-memory SQLite, faked Alpha Vantage)
├── frontend/
│   └── src/
│       ├── pages/               # Dashboard, Search, StockDetail, Watchlist, Reports, Profile, auth pages
│       ├── layouts/             # MainLayout (auth guard + nav), AuthLayout
│       ├── contexts/            # AuthContext
│       └── services/apiService.js  # Axios client: auth header, token refresh, API calls
├── docs/API.md                  # endpoint reference
└── .github/workflows/ci.yml
```

The full endpoint list with examples is in [docs/API.md](docs/API.md).

## Technical highlights

### A market-data client that copes with a free-tier API

Everything goes through [`services/alpha_vantage.py`](backend/src/services/alpha_vantage.py).

- **Errors arrive with HTTP 200.** Alpha Vantage reports rate limits and bad keys as a successful response with a `Note`/`Information` field in the body. The client checks the body, raises typed exceptions (`RateLimitError`, `AlphaVantageError`) and lets the app turn them into `503`/`502` responses with a useful message, instead of a misleading "no data".
- **Built around the quota.** The free tier allows 25 requests a day and about 1 per second.
  - Responses are cached per app for 5 minutes, and outgoing calls are serialised at least 1.1s apart behind a lock, so concurrent page loads don't trip the burst limit.
  - Reports are capped at 5 symbols.
  - Symbol-search hits are written to the `stocks` table, so repeat searches never leave the database.
- **Graceful degradation.** When `GLOBAL_QUOTE` comes back empty, the quote is rebuilt from the two latest daily bars, with change and % change derived from the previous close.

### JWT authentication with real logout

- Short-lived access tokens (1h) plus refresh tokens (30d), via Flask-JWT-Extended.
- **Revocation:** logout revokes *both* tokens, and a `token_in_blocklist_loader` rejects them afterwards. The blocklist is in memory to keep the demo dependency-free; a multi-process deployment would use Redis or a table with a TTL.
- **Silent refresh:** an Axios response interceptor catches a `401`, trades the refresh token for a new access token and retries the request once. Concurrent failures share a single refresh call.
- A `user_lookup_loader` exposes `current_user` to every route. Changing a password requires the current one.

### API design

- **App factory** (`create_app(overrides)`). Configuration comes from the environment, the app refuses to start without real secrets outside debug mode, and tests build isolated apps with overrides.
- **Versioned REST API** under `/api/v1`, one blueprint per resource, with a single JSON error shape (`{"message": ...}`) for every HTTP error.
- **One process can serve both the SPA and the API.** Unknown `/api/*` paths return JSON 404s, while every other path falls back to `index.html` for React Router.

### Testing and tooling

- **47 pytest tests**, each running against a fresh in-memory SQLite app.
- Alpha Vantage is faked at the HTTP boundary, so the real parsing, error mapping, caching and throttling code runs in the tests.
- Many tests are regression tests for bugs found while preparing this repo, for example password changes being silently ignored and weekly history reading the wrong response key.
- Ruff, ESLint and Prettier keep the code consistent, and GitHub Actions runs everything on each push.

## What I learned

- **Validate a third-party response's body, not just its status code.** Treating Alpha Vantage's HTTP 200 rate-limit messages as "no data" hid the real problem.
- **Free-tier limits shape the architecture.** Caching, throttling and input caps were what made the app usable on 25 requests a day.
- **Stateless tokens still need server state for logout.** A JWT stays valid until it expires unless you keep a blocklist, and choosing where that blocklist lives is a real trade-off.
- **Frontend/backend contract drift fails silently.** Several features "worked" in the UI while the API ignored mismatched field names. Tests at the API boundary now pin those contracts down.

## Known limitations

- **ASX coverage:** Alpha Vantage's free tier doesn't return quotes or history for ASX (`.AX`) listings. Seeded ASX companies show up in search and on the dashboard, but live data works for symbols Alpha Vantage covers, such as `IBM`, `MSFT`, NYSE-listed `BHP` or `BHP.LON`.
- **Notifications:** preferences are stored, but no notifications are sent yet.
- **Schema changes:** tables are created with `db.create_all()`; there are no migrations yet.
- **Revoked tokens:** they are kept in process memory, so they reset on restart.

## License

[MIT](LICENSE)
