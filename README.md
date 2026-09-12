# Handwritten Math Renderer

React/Vite frontend for rendering LaTeX and tokenized mathematical expressions as handwritten-style SVG. The application uses an Express server to call the Python parser and layout engine.

> **Security status:** This project is not ready for public multi-user deployment. Read [SECURITY.md](SECURITY.md) before exposing the server to untrusted traffic.

## Stack

- React and Vite for the interface.
- Express and `tsx` for the local API server.
- Python parser and layout engine for formula rendering.
- pnpm for JavaScript dependency management.

## Run locally

Prerequisites:

- Node.js 20 or newer.
- pnpm 11 or newer.
- Python 3.10 or newer.

Install the JavaScript dependencies:

```bash
pnpm install
```

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the application:

```bash
pnpm dev
```

Open `http://localhost:3000` unless the server reports a different port.

## Validation

```bash
pnpm run lint
pnpm run build
pytest -q
```

The project currently requires no environment variables. Keep any future server-only secrets out of Vite and never commit a real `.env` file. The placeholder file is [`.env.example`](.env.example).

## Security

The current release contains documented pending security work around custom SVG sanitization, API access control, request limits, process isolation, production middleware, and dependency updates. See [SECURITY.md](SECURITY.md) before deployment.
