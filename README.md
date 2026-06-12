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

Codex:

```bash
git clone https://github.com/<your-org>/research-portal-harness.git
cd research-portal-harness
bash installer/install.sh
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
python3 skills/research-portal-harness/scripts/init_workspace.py ~/research-portal-workspace
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
examples/                         # Sanitized example configs
installer/install.sh              # Copies the skill into ~/.codex/skills or another target
```
