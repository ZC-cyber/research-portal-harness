---
name: research-portal-harness
description: Use when a user wants Codex or Claude Code to set up a local harness for acquiring subscribed broker and data-platform research resources from portals such as Goldman Sachs Marquee, Morgan Stanley Matrix, J.P. Morgan Markets, UBS/UBS Neo, Citi Velocity, BofA/BAML, Bernstein, Barclays Live, Jefferies, Evercore ISI, Wolfe, Melius, Capital IQ Pro, FactSet, or another authenticated research portal. Guides installation, local browser login, 2FA/CAPTCHA handling, connector recipe setup, download, dedupe, indexing, and export without storing passwords or bypassing access controls.
---

# Research Portal Harness

This skill guides a local, user-controlled acquisition workflow for research materials the user is already entitled to access.

## What This Skill Can Do

- Set up a local research-resource workspace.
- Connect broker and data-platform portals one by one using a visible local browser.
- Help the user complete SSO, password, 2FA, and CAPTCHA directly on the official portal page.
- Reuse a local browser profile after login.
- Configure portal recipes for search, download, exclusion rules, rate limits, and login validation.
- Download entitled PDFs, Excel models, transcripts, and other research files.
- Dedupe files by hash, keep manifests, index metadata, and export artifacts for downstream research agents.
- Use the bundled `rph` execution CLI when it is installed in the local Python environment.

## What This Skill Must Not Do

- Do not ask the user to paste passwords, one-time codes, recovery codes, or session cookies into chat.
- Do not store passwords or secrets in config files.
- Do not bypass access controls, CAPTCHA, paywalls, entitlement checks, or portal rate limits.
- Do not scrape domains outside the configured allowed domains.
- Do not promise that every portal will work without recipe tuning.

## First Message To The User

Start by explaining the harness in plain language:

> I can help you connect your subscribed research portals to a local acquisition workflow. I will open each official portal in a visible browser; you sign in there directly, including SSO, 2FA, or CAPTCHA. I only verify that the session works, store a local browser profile, and then use that session to search, download, dedupe, index, and export the research materials you are entitled to access.

Then ask for:

- Portals to connect first.
- Target research scope: tickers, companies, sectors, themes, date range, and file types.
- Preferred local workspace path if the current directory is not obvious.

## Standard Workflow

1. Inspect the current repo or workspace. If none exists, create one with `references/onboarding_flow.md`.
2. Check local prerequisites with `scripts/check_environment.py`.
3. Initialize a workspace with `scripts/init_workspace.py` when needed.
4. For each portal, create or update a recipe using `references/portal_recipe_schema.md`.
5. Run login-only first. Open a visible browser; the user signs in directly on the official portal.
6. If SSO, 2FA, email code, SMS code, push approval, or CAPTCHA appears, pause and let the user complete it in the browser. See `references/auth_and_2fa.md`.
7. Validate the session through URL patterns, visible selectors, and a lightweight research/search page probe.
8. Run dry-run search before bulk download. Show candidate titles, dates, file types, and relevance reasons.
9. Download with conservative limits, write a manifest, hash files, dedupe, and keep source attribution.
10. Index and export for downstream research agents.
11. If auth expires, fail clearly and rerun login-only with the smallest manual step.

## Portal Selection

Offer the common portal list in two groups:

Broker research:
- Goldman Sachs Marquee
- Morgan Stanley Matrix
- J.P. Morgan Markets / Research
- UBS Research / UBS Neo
- Citi Velocity
- BofA / BAML Research
- Bernstein Research
- Barclays Live
- Jefferies Research
- Evercore ISI
- Wolfe Research
- Melius Research
- Other broker portal

Data platforms:
- Capital IQ Pro
- FactSet
- Other data platform

Ask the user to paste the official login URL for a portal if the recipe does not already exist locally. Treat remembered domain guesses as hints only; verify against the user's actual portal.

## When To Read References

- `references/onboarding_flow.md`: installing or initializing a new harness.
- `references/portal_recipe_schema.md`: creating or editing portal configs.
- `references/auth_and_2fa.md`: handling login, SSO, 2FA, CAPTCHA, expired sessions, and user handoff.
- `references/portal_patterns.md`: choosing portal-specific acquisition patterns and first-pass defaults.
- `references/compliance_guardrails.md`: checking safety, entitlement, attribution, rate-limit, and storage boundaries.

## Existing Workspace Pattern

When this skill is used inside an existing acquisition workspace, prefer its local scripts and config:

```bash
rph init <workspace>
rph add-portal <portal_id> --name "<Portal Name>" --login-url "<official_url>" --allowed-domain "<domain>" --workspace <workspace>
rph login <portal_id> --workspace <workspace>
rph search <portal_id> --task <task_id> --workspace <workspace>
rph fetch <portal_id> --task <task_id> --workspace <workspace> --max-downloads 10
rph index --task <task_id> --workspace <workspace>
rph status --task <task_id> --workspace <workspace>
```

If an older workspace has custom scripts, prefer them when they already encode portal-specific logic:

```bash
python3 -m playwright install chromium
python3 scripts/fetch_task.py <task_id> --brokers <portal_id> --login-only
python3 scripts/fetch_task.py <task_id> --brokers <portal_id>
python3 scripts/index_task.py <task_id>
python3 scripts/status_report.py <task_id>
```

Use the workspace's existing `config/brokers.json`, `config/tasks.json`, `data/state/`, `data/raw/`, `data/indexes/`, and manifest patterns instead of inventing a parallel structure.

The bundled generic downloader is link-based. If a portal hides materials behind viewer APIs, JavaScript-only buttons, or entitlement-specific document endpoints, create a portal-specific extension rather than bypassing controls.
