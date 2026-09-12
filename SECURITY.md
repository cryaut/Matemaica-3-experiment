# Security Status

This project is not yet ready to be deployed as a public multi-user service.

## Fixed in this pass

- Removed the local `.env` file that contained a Gemini API key.
- Removed the Vite configuration that could inject `GEMINI_API_KEY` into the browser bundle.
- Removed unused Gemini and dotenv packages from the client project.
- Added ignore rules for local sessions, package caches, Python caches, editor settings, and request captures.

The previously exposed Gemini key must still be revoked in Google AI Studio or Google Cloud. Do not reuse it.

## Pending security fixes before public deployment

- Sanitize custom SVG input before rendering it. The frontend currently renders SVG strings with `dangerouslySetInnerHTML`, and the API accepts custom symbol markup from requests.
- Add authentication or an equivalent access boundary for `/api/render`.
- Add request schema validation, strict body limits, rate limiting, process timeouts, and concurrency limits. Rendering currently starts a Python process per request.
- Stop logging request content and add security headers/content security policy.
- Ensure production deployments never expose Vite development middleware.
- Upgrade and re-audit JavaScript and Python dependencies before release.

Until these items are addressed, keep the service on a trusted local network and do not accept untrusted public traffic.
