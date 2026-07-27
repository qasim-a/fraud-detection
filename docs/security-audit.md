# Security and Data Audit

Audit date: 2026-07-27

## Scope and method

The repository source, tracked fixtures, structured-log redaction rules, ignored artifact paths,
environment templates, and committed history were reviewed for credentials, payment-card patterns,
private keys, access tokens, and identifying financial records. Configuration contains documented
local-only defaults; `.env` and generated `artifacts/` are ignored.

## Findings

- All committed accounts, merchants, devices, IP hashes, transactions, and analyst identities are
  visibly synthetic or deterministic UUID fixtures.
- No real card numbers, bank-account numbers, customer names, addresses, emails, or payment
  credentials are required or committed.
- Logging redacts configured sensitive keys and reports pipeline failures by exception class rather
  than serializing input records.
- Database access uses SQLAlchemy-bound values; secrets enter through ignored environment settings.
- Model and dataset artifacts are generated locally and excluded from Git.
- The only payment-card-like values found are the standard `4111111111111111` test value in two
  negative/redaction unit tests; it is never accepted by the transaction contract or used as data.

No identifying financial data or repository secret was found. This is a source audit, not a claim
of production certification or penetration testing. Repeat secret scanning before every public
release and rotate any credential immediately if it is ever committed.
