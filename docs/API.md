# API reference

Base URL: `http://127.0.0.1:5000/api/v1` (or `/api/v1` through the Vite dev server).

All request and response bodies are JSON. Errors always look like `{"message": "..."}`.
Endpoints marked 🔒 need an access token in the header: `Authorization: Bearer <access_token>`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/signup` | | Create an account |
| POST | `/auth/login` | | Get access + refresh tokens |
| POST | `/auth/refresh` | refresh token | Get a new access token |
| POST | `/auth/logout` | access or refresh token | Revoke the presented token |
| GET | `/users/me` | 🔒 | Current user's profile |
| PUT | `/users/me` | 🔒 | Update username, email or password |
| GET | `/stocks` | | Search stocks (local cache first, then Alpha Vantage) |
| GET | `/stocks/<symbol>` | | Company info plus the latest quote |
| GET | `/stocks/<symbol>/historical` | | OHLCV bars, newest first |
| GET | `/watchlist` | 🔒 | The user's watchlist |
| POST | `/watchlist` | 🔒 | Add a stock |
| DELETE | `/watchlist/<symbol>` | 🔒 | Remove a stock |
| GET | `/preferences` | 🔒 | Notification preferences (created with defaults on first read) |
| PUT | `/preferences` | 🔒 | Update preferences |
| POST | `/reports/build` | 🔒 | Compare stocks over a period |
| GET | `/saved-data` | 🔒 | The user's saved notes, optionally filtered by `?stock_symbol=` |
| POST | `/saved-data` | 🔒 | Save a note or value against a stock |
| DELETE | `/saved-data/<id>` | 🔒 | Delete one of the user's saved items |

## Authentication

Access tokens last 1 hour and refresh tokens 30 days. The frontend refreshes expired access tokens automatically. Logging out revokes both tokens: call `/auth/logout` once with each.

```http
POST /auth/signup
{"username": "alice", "email": "alice@example.com", "password": "at-least-8-chars"}

201 {"message": "User created successfully", "user_id": 1}
```

```http
POST /auth/login
{"email": "alice@example.com", "password": "at-least-8-chars"}

200 {"message": "Login successful", "access_token": "eyJ...", "refresh_token": "eyJ...", "user_id": 1}
```

```http
POST /auth/refresh
Authorization: Bearer <refresh_token>

200 {"access_token": "eyJ..."}
```

Revoked or expired tokens get `401`.

## Users

```http
PUT /users/me  🔒
{"username": "alice2", "current_password": "old-password", "new_password": "new-password"}

200 {"message": "User updated successfully", "user": {"id": 1, "username": "alice2", "email": "...", ...}}
```

Every field is optional. Changing the password requires `current_password` (`403` if it's wrong). New passwords need at least 8 characters.

## Stocks

`GET /stocks?search_term=BHP&exchange=ASX&limit=10&offset=0`

The endpoint searches the local `stocks` table first. If nothing matches, it asks Alpha Vantage's symbol search and caches the matches locally.

```json
{"total": 1, "limit": 10, "offset": 0, "data": [{"id": 1, "symbol": "BHP.AX", "name": "BHP Group Limited", "exchange": "ASX", "last_updated": null}]}
```

`GET /stocks/IBM` returns the stored company info merged with the latest quote: `current_price`, `open_price`, `day_high`, `day_low`, `volume`, `previous_close`, `change`, `change_percent` and `last_updated`.

`GET /stocks/IBM/historical?interval=weekly` takes `interval` (`daily`, `weekly` or `monthly`) and returns `[{"date", "open", "high", "low", "close", "volume"}, ...]`.

When Alpha Vantage is rate-limiting, these endpoints return `503`. If it is unreachable or no API key is configured, they return `502`.

## Watchlist

```http
POST /watchlist  🔒
{"stock_symbol": "IBM"}

201 {"message": "Stock added to watchlist", "watchlist_item": {"id": 1, "symbol": "IBM", "name": "...", "exchange": "...", "added_at": "..."}}
```

You can only add stocks that exist in the local `stocks` table, which happens after they are searched or viewed (`404` otherwise). Adding the same stock twice returns `409`.

## Preferences

```http
PUT /preferences  🔒
{"notification_frequency": "weekly", "notification_type_email": true, "notification_type_inapp": false}
```

`notification_frequency` is one of `daily`, `weekly` or `realtime_critical`. Any other value returns `400`.

## Reports

```http
POST /reports/build  🔒
{"stock_symbols": ["IBM", "MSFT"], "data_fields": ["price", "volume", "change"], "time_period": "1month"}
```

- `time_period`: `1week`, `1month`, `3months`, `6months`, `1year` or `5years`. Periods longer than 3 months use weekly bars.
- A report can include at most 5 symbols, because each one costs an Alpha Vantage request.

```json
{
  "time_period": "1month",
  "interval": "daily",
  "data_fields": ["price", "volume", "change"],
  "generated_at": "2026-10-27T05:00:00+00:00",
  "results": [
    {"symbol": "IBM", "from": "2026-09-26", "to": "2026-10-26", "latest_close": 253.44, "period_high": 256.3,
     "period_low": 217.79, "average_volume": 5884065, "change": 27.8, "change_percent": 12.49},
    {"symbol": "NOPE", "error": "No data available"}
  ]
}
```

## Saved data

```http
POST /saved-data  🔒
{"stock_symbol": "IBM", "data_point_name": "note", "data_value": "Check earnings date"}
```

Items are scoped to the signed-in user. Another user's item behaves as if it doesn't exist (`404`).

## Trying it with Postman

1. Create an environment with `base_url = http://127.0.0.1:5000/api/v1`.
2. Add this test script to the login request, so later requests can use `{{access_token}}`:

```javascript
const body = pm.response.json();
pm.environment.set('access_token', body.access_token);
pm.environment.set('refresh_token', body.refresh_token);
```
