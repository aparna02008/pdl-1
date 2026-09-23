# CiviSense — Admin Panel

Separate app from the citizen frontend. Runs on its own port so both can run at the same time.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Runs on `http://localhost:5175` by default (set in `vite.config.js`).

Set `VITE_API_URL` in `.env` to match whatever port your backend is actually running on (`8000` or `8001` — whichever you started uvicorn with).

## What's here

- Stats row — total / submitted / in progress / resolved. Pulled from `GET /complaints/stats/summary`. If that endpoint isn't available, falls back to counting loaded complaints rather than showing a fake number.
- **Needs attention** section — everything not yet resolved (`submitted` + `in_progress`).
- **Resolved** section — everything marked resolved.
- Status filter and issue-type filter.
- Inline status dropdown per row — calls `PATCH /complaints/{id}/status` directly, with optimistic UI update that rolls back if the request fails.
- AI fields (issue type, priority) show "AI: unavailable" / "Not available" honestly when the backend hasn't produced them yet — never a placeholder value.

## Required backend endpoints

- `GET /complaints?status=&issue_type=`
- `GET /complaints/stats/summary`
- `PATCH /complaints/{id}/status`
