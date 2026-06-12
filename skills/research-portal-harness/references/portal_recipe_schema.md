# Portal Recipe Schema

Use a JSON or YAML recipe per portal. In an acquisition workspace, map this to `config/brokers.json`.

## Required Fields

```json
{
  "id": "bernstein_research",
  "name": "Bernstein Research",
  "allowed_domains": ["example.com"],
  "start_urls": ["https://example.com/"],
  "manual_login": true,
  "headless": false,
  "manual_login_timeout_ms": 300000,
  "wait_until": "domcontentloaded",
  "wait_after_load_ms": 5000
}
```

Rules:

- `id`: stable lowercase snake-case identifier.
- `name`: user-facing portal name.
- `allowed_domains`: only domains the user is entitled to access through this portal.
- `start_urls`: official login or research landing URLs.
- `manual_login`: should be true for broker and data portals.
- `headless`: should be false for login and first validation.

## Authentication Validation

Add both pending and success indicators when possible:

```json
{
  "auth_pending_url_patterns": ["login", "signin", "mfa", "sso"],
  "auth_success_url_patterns": ["research", "markets", "portal"],
  "auth_pending_selectors": ["input[type='password']", "text=Sign In"],
  "auth_success_selectors": ["text=Research", "text=Search"]
}
```

Prefer indicators observed in the user's current portal session over generic guesses.

## Search And Download

Use portal-specific sections when needed:

```json
{
  "research_search": {
    "enabled": true,
    "max_reports_per_company": 10,
    "max_reports_per_industry_term": 10,
    "date_range_days": 730
  },
  "download_selectors": [
    "a[download]",
    "a[href*='download' i]",
    "button:has-text('Download')",
    "button:has-text('PDF')",
    "button:has-text('Excel')"
  ],
  "exclude_url_patterns": ["privacy", "terms", "logout"],
  "exclude_title_patterns": ["Global Research Directory"],
  "rate_limit": {
    "min_delay_ms": 1500,
    "max_downloads_per_run": 50
  }
}
```

## Task Scope

Keep task scope separate from portal identity:

```json
{
  "id": "ai_networking_optics",
  "tickers": ["MRVL", "ANET", "LITE", "COHR"],
  "company_terms": ["Marvell", "Arista", "Lumentum", "Coherent"],
  "industry_terms": ["AI networking", "optical transceiver", "800G", "1.6T"],
  "file_types": ["pdf", "xlsx", "xlsm"],
  "date_range_days": 730
}
```

## Validation Checklist

- Allowed domains match the user's visible browser URLs.
- Login validation does not depend on passwords or cookies pasted into chat.
- Download selectors do not capture legal/privacy/logout pages.
- First run has conservative max downloads.
- Every downloaded file has source attribution and SHA256.
