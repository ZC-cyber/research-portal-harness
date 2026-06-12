# Auth And 2FA Handling

The agent coordinates login; the user performs login.

## Allowed Flow

1. Open a visible local browser to the official portal URL.
2. Tell the user to complete username, password, SSO, 2FA, push approval, email code, SMS code, or CAPTCHA directly in that browser.
3. Poll for success with URL patterns, selectors, and lightweight page probes.
4. Store only local browser profile state on disk.
5. Continue with search or download after validation passes.

## Disallowed Flow

- Do not ask the user to paste usernames plus passwords into chat.
- Do not ask for one-time codes, backup codes, cookies, localStorage, session tokens, or exported profiles.
- Do not automate CAPTCHA solving or bypass portal controls.
- Do not use another person's account or shared credentials.

## User-Facing Login Prompt

Use language like:

> I opened the official portal in a visible browser. Please sign in there directly. If you see SSO, Duo, SMS/email verification, or CAPTCHA, complete it in the browser. I will wait and only check whether the session reaches the research area.

## Expired Session

If the session expires:

1. Stop downloads.
2. Report the portal name and sanitized current URL.
3. Say that the session needs refresh.
4. Rerun login-only for that portal.
5. Resume from manifest state, skipping already downloaded hashes.

## Validation Signals

Strong signals:

- Research search page loads.
- User name or account menu is visible.
- Search input or report table is visible.
- A lightweight search returns entitled results.

Weak signals:

- URL changed away from login.
- A generic home page loads.
- Cookies exist.

Do not treat weak signals alone as enough for bulk download.

