# AI Customer Support

Supabase-backed email support pipeline that polls Gmail, creates tickets, and saves messages.

## Deployment

This project is deployed for free using **Render** (API) and **GitHub Actions** (scheduled poller).

### Live links

- **API health check:** `https://<your-render-service>.onrender.com/health`
- **GitHub repo:** `https://github.com/<your-username>/ai-customer-support`
- **Poller:** Runs automatically every 15 minutes via GitHub Actions (`.github/workflows/poller.yml`)

### Tech stack

- FastAPI (API)
- Python + uv (runtime + dependency management)
- Docker (containerized via Render)
- Supabase (PostgreSQL database)
- Gmail API (email reading/replying)
- Google Gemini (LLM classification + reply drafting)
- GitHub Actions (scheduled background poller)
- Render (free tier web service)

### Environment variables

Set these in **Render dashboard → Environment Variables** (API) and **GitHub → Settings → Secrets and variables → Actions** (poller):

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Gmail OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Gmail OAuth client secret |
| `GOOGLE_REFRESH_TOKEN` | Gmail OAuth refresh token |
| `DATABASE_URL` | Supabase connection string (URI) |
| `LLM_API_KEY` | Gemini / Google AI Studio API key |
| `POLL_INTERVAL_SECONDS` | Poll frequency (default `60`) |
| `DASHBOARD_USERNAME` | Admin username (default `admin`) |
| `DASHBOARD_PASSWORD` | Admin password |
| `PYDANTIC_AI_NO_BANNER` | `1` |

### Updating the deployment

```powershell
git add .
git commit -m "describe your change"
git push origin main
```

Render auto-rebuilds the API on push. GitHub Actions runs the latest code on the next scheduled poller run (or manual trigger).

---

## Prerequisites

- [Supabase CLI](https://supabase.com/cli) installed and logged in (`supabase login`)
- [uv](https://github.com/astral-sh/uv) installed
- Docker running (for local Supabase stack)
- A `.env` file in this directory with your Supabase database URL and Gmail OAuth credentials

## Supabase CLI

Link the remote project (already done):

```powershell
supabase login
supabase init
supabase link --project-ref <project-ref>
```

## Database Migrations

Apply migrations to the **remote** Supabase project:

```powershell
supabase db push --remote
```

Apply migrations to the **local** stack:

```powershell
supabase db push
```

Resetting the database:

```powershell
supabase db reset --remote
```


## Knowledge Base

The knowledge base is seeded from Markdown files into the Supabase `knowledge_base` table.

### Seed the knowledge base

Run the seed script to parse the markdown files and insert/update rows:

```powershell
uv run python -m scripts.seed_knowledge_base
```

Expected output:

```
brand-and-tone: 3 entries
escalation-rules: 2 entries
paddle-boards: 5 entries
returns-and-warranty: 3 entries
shelving: 4 entries
shipping: 3 entries
```

Running the script again updates existing rows instead of duplicating them.

## Evaluate the AI Agent

The eval suite runs 18 golden emails through the agent's `decide()` pipeline and checks
that the classifier picks the right section and the agent takes the right action
(`reply` vs `escalate`).

```powershell
uv run python -m app.evals.run_evals
```

Test cases cover:
- Paddle boards: size recommendations, missing accessories, slow leaks, seam splits
- Shelving: missing hardware, cracked panels, wrong finishes
- Returns & warranty, shipping, prompt-injection and unknown topics (always escalate)

The report prints each case with the expected vs actual section and action,
and highlights any mismatches.

## Run the Poller

From the `ai-customer-support` directory:

```powershell
uv run python -m app.poller
```

The poller checks Gmail every 30 seconds, processes new inbox messages, and writes them to Supabase.

## Run the FastAPI App

```powershell
uv run uvicorn app.main:app --reload
```

Health check: `http://localhost:8000/health`

## Install / Sync Dependencies

```powershell
uv sync
```