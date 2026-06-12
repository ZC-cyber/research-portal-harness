# Portal Patterns

Portal-specific details drift. Treat these as acquisition patterns, not permanent facts. Prefer the user's visible portal URL and current DOM over memory.

## Broker Research Portals

Common targets:

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

Typical workflow:

1. Login with visible browser and manual 2FA.
2. Navigate to research search or company page.
3. Search by ticker, company name, analyst, or industry term.
4. Filter by date range and asset class if available.
5. Open candidate report pages.
6. Download PDF and model attachments.
7. Deduplicate by SHA256 and source URL.

Common file types:

- `.pdf`: reports, notes, primers, transcripts.
- `.xlsx`, `.xls`, `.xlsm`: models and data tables.
- `.csv`, `.json`, `.zip`: exports or platform-specific bundles.

Common false positives:

- Global research directories.
- Legal disclosures.
- Terms, privacy, support, and logout pages.
- Structured product notes unrelated to equity research.
- Marketing pages for non-entitled users.

## Data Platforms

Common targets:

- Capital IQ Pro
- FactSet

Typical workflow:

1. Login with visible browser and manual 2FA.
2. Validate entitlement to documents, transcripts, filings, or research aggregation.
3. Prefer official export/download endpoints exposed by the platform UI.
4. For research aggregation, keep original publisher, platform source, document id, date, and entitlement context.
5. For transcripts or company documents, preserve company, event date, filing URL or document URL, and platform document id.

## Other Portal

For unknown portals:

1. Ask the user for official login URL.
2. Create a minimal manual-login recipe.
3. Run login-only and observe post-login URL/domain.
4. Add allowed domains only after observing them.
5. Dry-run search before download.
6. Keep first download budget small.

