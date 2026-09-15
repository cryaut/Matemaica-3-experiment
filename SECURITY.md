# Security Notice

This project is not yet ready to be deployed as a public multi-user service.

## Before public deployment

- Treat custom handwritten symbols as untrusted input until their SVG content is safely sanitized.
- Protect the rendering endpoint with authentication or another trusted access boundary.
- Add input validation, request-size limits, rate limiting, timeouts, and concurrency limits.
- Avoid sending sensitive personal information or private documents through the service.
- Use production middleware only, with security headers and an appropriate content security policy.
- Upgrade and re-audit JavaScript and Python dependencies before release.

Until these protections are in place, keep the service on a trusted local network and do not accept untrusted public traffic.
