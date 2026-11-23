# AI Customer Support

Supabase-backed email support pipeline that polls Gmail, creates tickets, and saves messages.

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