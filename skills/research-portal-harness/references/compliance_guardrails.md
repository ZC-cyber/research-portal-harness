# Compliance Guardrails

Use this checklist before enabling bulk download.

## Entitlement

- The user must have legitimate access to the portal and materials.
- Do not bypass access controls, paywalls, CAPTCHA, or entitlement checks.
- Do not use credentials supplied in chat.
- Do not distribute downloaded research outside the user's permitted use.

## Storage

- Store downloads locally by default.
- Store browser profiles locally under a clear `data/state/browser_profiles/` path.
- Store manifests and indexes without passwords, tokens, or cookies.
- Redact query parameters from user-facing logs when they may contain session details.

## Rate Limits

- Use conservative first-run limits.
- Add delays between downloads.
- Stop when the portal shows throttling, unusual security prompts, or access warnings.
- Prefer recoverable manifests so repeated runs do not redownload the same files.

## Attribution

Every downloaded or indexed artifact should retain:

- Portal or broker name.
- Original URL or document id.
- Title.
- Published date if available.
- Analyst/source if available.
- Local path.
- SHA256.
- Download timestamp.

## Failure Behavior

Fail clearly when:

- Login expires.
- Entitlement is missing.
- Download selectors no longer work.
- Search results are unexpectedly noisy.
- The portal redirects to support, legal, demo, or marketing pages.

When failing, recommend the smallest next manual step: refresh login, paste official URL, reduce scope, or inspect one page.

