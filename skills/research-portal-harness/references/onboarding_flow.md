# Onboarding Flow

Use this flow when the user is installing the harness or connecting the first portal.

## 1. Explain The Boundary

Tell the user:

- The harness runs locally.
- The user signs in directly on official portal pages.
- The harness stores browser profile state, not passwords.
- Downloaded files remain local unless the user explicitly exports or syncs them.
- The workflow only applies to resources the user is entitled to access.

## 2. Check Environment

Run:

```bash
python3 skills/research-portal-harness/scripts/check_environment.py
```

If Playwright browsers are missing, install Chromium:

```bash
python3 -m playwright install chromium
```

If the default `python3` is older than 3.11 and `uv` is available:

```bash
uv python install 3.11
uv venv --python 3.11
source .venv/bin/activate
```

For an existing Python acquisition workspace, install editable dependencies from that workspace root:

```bash
python3 -m pip install -e ".[dev]"
```

## 3. Initialize Workspace

For a standalone workspace:

```bash
python3 skills/research-portal-harness/scripts/init_workspace.py ~/research-portal-workspace
```

For the existing repo, use the current repo root and preserve existing `config/`, `data/`, and `scripts/`.

## 4. Choose Portals

Offer the grouped list from `SKILL.md`. For each selected portal, collect:

- Human-readable portal name.
- Official login URL or landing page URL.
- Known allowed domains from the user-visible URL bar after login.
- Research scope: tickers, companies, industry terms, date range, file types.
- Download budget for the first run.

Do not collect passwords, one-time codes, recovery codes, cookies, or exported browser profiles.

## 5. Login-Only Pass

Open the portal in a visible browser. The user completes login directly in the browser. Validate success with:

- URL no longer matches login or MFA patterns.
- Research/search/navigation selectors are visible.
- A lightweight search or landing-page probe succeeds.

If validation fails, report the current sanitized URL and which condition failed.

## 6. Dry Run Before Download

Search first and show candidates. Include:

- Portal name.
- Title.
- Published date if available.
- Analyst/source if available.
- File type.
- Why it matched.

Ask the user before bulk download if the result set looks noisy or unexpectedly large.

## 7. Fetch, Dedupe, Index, Export

Download conservatively. Keep a manifest with source URL, title, portal, local path, SHA256, size, and downloaded timestamp. Index after fetch. Export only when the user asks or the repo's workflow expects it.
