# HalluGuard Frontend

A production‑ready React + Vite frontend for the AI Hallucination Detection project.

## Features
- Chat UI with model selector
- Real‑time hallucination analysis panel
- Dark futuristic theme (black, red, blue) with subtle glow effects
- Responsive layout (sidebar, top‑bar, chat & analysis panels)
- Mock API for development (no API keys needed)
- Toast notifications and loading spinners

## Tech Stack
- React 18 + TypeScript
- Vite
- Tailwind CSS (dark mode, custom colors)
- Lucide React icons

## Project Structure
```
frontend/
  src/
    components/
      chat/
      analysis/
      common/
      Sidebar.tsx
      TopBar.tsx
    context/
    services/
    types.ts
    App.tsx
    main.tsx
    index.css
  vite.config.ts
  tailwind.config.cjs
  postcss.config.cjs
  tsconfig.json
  package.json
```

## Development
```bash
npm install
npm run dev
```
Open http://localhost:5173 in a browser.

## Build & Preview
```bash
npm run build   # builds to ./dist
npm run preview # serves the built app locally
```

## API Integration
The frontend expects a backend endpoint:
```
POST /api/chat
{ "model": "...", "message": "...", "conversation_id": "..." }
```
The response must contain `answer`, `claims`, and `analysis` matching the mock shape defined in `src/services/api.ts`. When connecting to a real backend, ensure the proxy in `vite.config.ts` points to the correct server URL.

---
*No API keys are stored in the frontend.*
