# React Frontend for AI Email Assistant

This Vite + React + TypeScript project consumes the FastAPI backend exposed at
`/email/generate`.

## Getting started

```powershell
# From the repository root
cd frontend
npm install

# Start the dev server (http://localhost:5173)

```

Ensure the FastAPI backend is running locally (see top-level `README.md`):

```powershell
uvicorn src.api.main:app --reload --port 8001
```

## Configuration

The app reads `VITE_API_BASE_URL` from `.env.development`. For local development
this is already set to `http://localhost:8001`. Adjust as needed for staging or
production deployments.

## Available scripts

- `npm run dev` – start the Vite dev server
- `npm run build` – production build
- `npm run preview` – serve the production build locally
- `npm run lint` – run ESLint checks

## Next steps

- Implement OAuth routes (`/auth/callback`) using React Router and connect to
  the backend OAuth endpoints.
- Add authenticated flows (profile editor, history view) using additional API
  routes.
- Integrate design system components or TailwindCSS for production styling.
])
