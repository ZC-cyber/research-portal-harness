# Research Portal Harness

Codex / Claude Code skill for setting up a local, user-controlled workflow that acquires research materials from subscribed broker and data-platform portals.

The harness opens each official portal in a visible local browser. You sign in directly on the portal, including SSO, 2FA, SMS/email verification, push approval, or CAPTCHA. The skill verifies the session, stores only a local browser profile, and then uses that authenticated session to search, download, dedupe, index, and export research materials you are entitled to access.

## Supported Portal Families

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
- Other broker portals

Data platforms:

- Capital IQ Pro
- FactSet
- Other data platforms

## Install

Install the skill:

```bash
git clone https://github.com/ZC-cyber/research-portal-harness.git
cd research-portal-harness
bash installer/install.sh
```

Install the execution CLI:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
python3 -m playwright install chromium
```

Claude Code:

```bash
bash installer/install.sh ~/.claude/skills
```

Then invoke:

```text
Use $research-portal-harness to connect my subscribed research portals.
```

## Local Workspace

The skill can initialize a separate acquisition workspace:

```bash
python3 skills/research-portal-harness/scripts/check_environment.py
rph init ~/research-portal-workspace
```

Before running a real Playwright/PDF/Excel acquisition workflow, use the stricter runtime check:

```bash
python3 skills/research-portal-harness/scripts/check_environment.py --strict-runtime
```

## Execution CLI

The first execution layer is intentionally local and conservative. It can:

- create workspace config and state directories
- add portal recipes
- open a visible browser for manual login and 2FA
- discover candidate report/model/data links from allowed domains
- batch download PDFs, Excel models, CSV/JSON/ZIP exports
- dedupe by URL and SHA256
- build a basic JSONL index with PDF text previews and Excel sheet metadata
- report manifest and index status

Example:

```bash
rph init ~/research-portal-workspace
rph safety-ack --workspace ~/research-portal-workspace
rph setup \
  --workspace ~/research-portal-workspace \
  --portal-id bernstein_research \
  --name "Bernstein Research" \
  --login-url "https://research.example.com/login" \
  --allowed-domain "example.com" \
  --acknowledge-safety
rph doctor bernstein_research --workspace ~/research-portal-workspace
rph login bernstein_research --workspace ~/research-portal-workspace
rph search bernstein_research --task example_research_task --workspace ~/research-portal-workspace
rph fetch bernstein_research --task example_research_task --workspace ~/research-portal-workspace --max-downloads 10
rph index --task example_research_task --workspace ~/research-portal-workspace
rph status --task example_research_task --workspace ~/research-portal-workspace
```

This generic downloader is link-based. Portals that hide downloads behind viewer APIs, JavaScript-only buttons, or entitlement-specific document endpoints may need portal-specific recipe extensions.

Run the local end-to-end mock portal before connecting real subscriptions:

```bash
rph smoke-test
```

Use `examples/brokers.example.json` and `examples/tasks.example.json` as sanitized starting points. Do not commit real browser profiles, downloaded research, personal manifests, or session-bearing URLs.

## Safety Boundary

- Do not paste passwords, one-time codes, recovery codes, cookies, or session tokens into chat.
- Do not use this to bypass access controls, paywalls, CAPTCHA, entitlement checks, or portal rate limits.
- Only acquire materials you are entitled to access.
- Keep downloaded research local unless your license and compliance rules allow sharing.
- Store attribution for every downloaded file: portal, source URL or document id, title, local path, hash, and timestamp.

## Repository Contents

```text
skills/research-portal-harness/   # Skill package for Codex / Claude Code
src/research_portal_harness/       # Local execution CLI and library
tests/                             # Safety and smoke tests
examples/                         # Sanitized example configs
installer/install.sh              # Copies the skill into ~/.codex/skills or another target
```
