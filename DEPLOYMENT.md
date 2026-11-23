# Deployment Guide — Customer Support Automation

**Goal:** Put your email support project online for free without a credit card.  
**Tools:** Render (public API), GitHub Actions (background poller), Supabase (database).

---

## What you will have at the end

| Part | Where it runs | Cost | Credit card needed? |
|------|--------------|------|---------------------|
| API (website / health check) | Render free tier | Free | No |
| Poller (checks Gmail every 15 min) | GitHub Actions | Free | No |
| Database | Supabase | Free | No |

---

## Part 0 — Get everything ready before deploying

Do these steps **once** before you follow the deployment steps. Each step says **what to do** and **why**.

### 0.1 Create a GitHub account and push your code

**What to do**

1. Go to [github.com](https://github.com) and create a free account if you do not have one.
2. Sign in, click the **+** icon in the top right → **New repository**.
3. Name it `ai-customer-support`.
4. Choose **Public**.
5. **Do not** check “Add a README file” or “Add .gitignore”.
6. Click **Create repository**.

Now push your local code. Open PowerShell in your project folder:

```powershell
cd D:\AI\ai-customer-support
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ai-customer-support.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

Replace `YOUR-USERNAME` with your actual GitHub username.

**Why**

Render needs to read your code from GitHub so it can build and host the app automatically. A public repository lets Render access it without extra configuration.

---

### 0.2 Create a Supabase project and get the Database URL

**What to do**

1. Go to [supabase.com](https://supabase.com) and sign up for a free account.
2. Click **New Project**.
3. Give it a name (for example, `customer-support`) and set a strong database password. Save this password somewhere safe.
4. Choose a region close to you.
5. Click **Create new project** and wait about 1–2 minutes while Supabase sets up your database.
6. Once ready, go to **Settings** → **Database**.
7. Under **Connection string**, find **URI** (it starts with `postgresql://`).
8. Copy the full string. It looks like:
   ```
   postgresql://postgres:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/db.xxxxxxxxxxxxxxxxx.supabase.co:5432/postgres
   ```
   Save this — you will paste it into Render and GitHub later as `DATABASE_URL`.

**Why**

Your app stores emails, tickets, and events in Supabase. Render needs the `DATABASE_URL` so the app can connect to your database over the internet.

> Optional: If your tables are not created yet, run these from your project folder:
> ```powershell
> supabase login
> supabase link --project-ref <your-project-ref>
> supabase db push --remote
> ```

---

### 0.3 Create Gmail OAuth credentials

Your app needs permission to read and send emails from your Gmail account. This happens in the Google Cloud Console.

**Step A: Create a Google Cloud project**

1. Go to [console.cloud.google.com](https://console.cloud.google.com).
2. Click the project selector at the top → **New Project**.
3. Name it `customer-support-automation` and click **Create**.
4. Make sure the new project is selected at the top of the page.

**Step B: Enable the Gmail API**

1. In the left menu, go to **APIs & Services** → **Library**.
2. Search for **Gmail API** and click it.
3. Click **Enable**.

**Step C: Configure the OAuth consent screen**

1. In the left menu, go to **APIs & Services** → **OAuth consent screen**.
2. Choose **External** and click **Create**.
3. Fill in:
   - **App name:** `Customer Support Automation`
   - **User support email:** your email address
   - **Developer contact information:** your email address
4. Click **Save and Continue**.
5. Skip the **Scopes** step (click **Save and Continue**).
6. Skip **Test users** (click **Save and Continue**).
7. Click **Back to Dashboard**.

**Step D: Create OAuth credentials**

1. In the left menu, go to **APIs & Services** → **Credentials**.
2. Click **Create credentials** → **OAuth client ID**.
3. Application type: **Desktop app**.
4. Name: `gmail-desktop`.
5. Click **Create**.
6. Copy your **Client ID** and **Client Secret** and save them somewhere safe.

**Step E: Get the Refresh Token**

You already have a helper script in your repo: `scripts/get_refresh_token.py`.

1. Make sure `credentials.json` is in your project folder (from the tutorial's Gmail setup). It is gitignored, so it will not be uploaded to GitHub.
2. Run the script locally:

```powershell
cd D:\AI\ai-customer-support
uv run python scripts/get_refresh_token.py
```

3. A browser window opens. Sign in with the Gmail account you want to use, and click **Allow**.
4. Copy the three values printed in the terminal:
   - `GOOGLE_CLIENT_ID=...`
   - `GOOGLE_CLIENT_SECRET=...`
   - `GOOGLE_REFRESH_TOKEN=...`
5. Save them safely — you will need them for Render and GitHub secrets.

**Is it a problem that `get_refresh_token.py` is on GitHub?**

No. The script itself is just code — it does not contain your secrets.

**Important:** Make sure `credentials.json` was **not** committed to GitHub. It is listed in `.gitignore`, so a normal `git add .` skips it. Check your GitHub repository page to confirm `credentials.json` is not there. If it is, remove it immediately.

### ⚠️ Safety rule — never run this in GitHub Actions

**Do not** run `scripts/get_refresh_token.py` in GitHub Actions or any public CI. It prints your client secret and refresh token to the terminal log, where anyone with access to the repository could see them.

The GitHub Actions workflow (`.github/workflows/poller.yml`) **does not** use this script. It reads the secrets directly from GitHub repository secrets, which is safe.

| Where | Is it safe to run `get_refresh_token.py`? |
|-------|-------------------------------------------|
| Your own computer (PowerShell / terminal) | ✅ Yes — run it once to get your tokens |
| GitHub Actions workflow | ❌ No — never |
| Render dashboard | ❌ No — never |

**Why**

- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` identify your app to Google.
- `GOOGLE_REFRESH_TOKEN` lets your deployed app read and send emails automatically, 24/7, without you logging in again.

---

### 0.4 Get an LLM API key (Gemini)

Your app uses a language model to classify emails and write replies. The tutorial uses Gemini from Google AI Studio.

**What to do**

1. Go to [aistudio.google.com](https://aistudio.google.com).
2. Sign in with your Google account.
3. Click **Get API key** in the left sidebar.
4. Click **Create API key** and copy the key it shows you.
5. Save it somewhere safe — you will paste it into Render and GitHub as `LLM_API_KEY`.

**Why**

The app needs this key to call the LLM (for example, to decide whether an email should be answered or escalated).

---

### 0.5 Install Docker Desktop (for local testing only)

You do not need Docker to deploy on Render, but it helps you test that your app builds correctly before you push.

**What to do**

1. Go to [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop).
2. Download Docker Desktop for Windows.
3. Run the installer and follow the prompts (you may need to restart your computer).
4. Open Docker Desktop and make sure it says **Docker is running**.
5. In PowerShell, verify it works:

```powershell
docker --version
docker compose version
```

**Why**

Docker packages your app into a container so it runs the same way on your laptop and on Render. You only need it to test locally; Render handles the Docker part for you after deployment.

---

### Quick checklist before you continue

Make sure you have copied these somewhere safe:

| Item | Where you got it |
|------|------------------|
| GitHub repo URL | `https://github.com/YOUR-USERNAME/ai-customer-support` |
| Supabase `DATABASE_URL` | Supabase → Settings → Database → URI |
| `GOOGLE_CLIENT_ID` | Google Cloud Console → Credentials |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console → Credentials |
| `GOOGLE_REFRESH_TOKEN` | From `get_token.py` output |
| `LLM_API_KEY` | Google AI Studio → API keys |

---

## Part 1 — Deploy the project

### Step 1: Add the Docker file

**What to do**

Create a new file in your project root: `D:\AI\ai-customer-support\Dockerfile`

Paste this:

```dockerfile
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY app ./app
ENV PATH="/app/.venv/bin:$PATH"

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Then create `.dockerignore` in the same folder and paste:

```
.env
.venv
.git
credentials.json
supabase
evals
knowledge_base
dashboard/node_modules
dashboard/dist
__pycache__/
*.pyc
```

**Why**

- **Dockerfile:** Tells Render how to build your app inside a container. It installs only the libraries you need (`--no-dev`) and starts the FastAPI server.
- **`$PORT`:** Render automatically tells your app which port to use. We write `$PORT` instead of a fixed number like `8080` so Render can assign it.
- **`.dockerignore`:** Keeps secrets (`.env`, `credentials.json`) and junk out of the image you upload to Render.

**Commit and push**

Open PowerShell in your project folder and run:

```powershell
cd D:\AI\ai-customer-support
git add Dockerfile .dockerignore
git commit -m "Add Dockerfile for Render deployment"
git push origin main
```

---

### Step 2: Create your Render account and deploy

**What to do**

1. Go to [render.com](https://render.com) and sign up with your GitHub account. **Do not add a credit card.** Choose the free plan when asked.
2. Click **New +** → **Web Service**.
3. Connect your GitHub account (if not already connected).
4. Select your repository `ai-customer-support`.
5. Choose branch `main`.
6. Render should detect the Dockerfile automatically. Set:
   - **Runtime:** Docker
   - **Instance type:** Free
7. Click **Advanced** at the bottom.
8. Under **Environment Variables**, add each of these (copy one row at a time):

| Key | Value |
|-----|-------|
| `GOOGLE_CLIENT_ID` | your Gmail client ID |
| `GOOGLE_CLIENT_SECRET` | your Gmail client secret |
| `GOOGLE_REFRESH_TOKEN` | your Gmail refresh token |
| `DATABASE_URL` | your Supabase connection string |
| `LLM_API_KEY` | your Gemini/LLM API key |
| `POLL_INTERVAL_SECONDS` | `60` |
| `DASHBOARD_USERNAME` | `admin` |
| `DASHBOARD_PASSWORD` | a strong password you make up |
| `PYDANTIC_AI_NO_BANNER` | `1` |

9. Click **Create Web Service**.

**Why**

- Render builds the Docker image from your GitHub code and hosts the API for you.
- **Environment Variables** are secret settings. Render injects them into your running app so your code can read Gmail, Supabase, and the LLM without you hard-coding passwords in the source.
- Free tier means Render may “spin down” (sleep) after 15 minutes of no visitors. The first person who opens your link wakes it up again — this is fine for a portfolio.

---

### Step 3: Wait for the build and verify the API

**What to do**

1. In the Render dashboard, click on your new web service.
2. Watch the **Deploy** log. Wait until it says **Live** or **Deployed**.
3. Render will show you a public URL, like:
   ```
   https://ai-customer-support.onrender.com
   ```
4. Open this in your browser and add `/health` at the end:
   ```
   https://ai-customer-support.onrender.com/health
   ```
5. You should see:
   ```json
   {"status":"ok"}
   ```

**Why**

The `/health` endpoint is a simple test page your app already has. If it returns `{"status":"ok"}`, your container is running, your environment variables are loaded, and the app can start.

---

### Step 4: Set up the poller with GitHub Actions

**What the poller does**

The poller checks Gmail for new emails, reads them, uses AI to decide what to do, sends replies if needed, and saves everything to Supabase. It should run automatically in the background.

Render’s free tier cannot run background workers 24/7, so we use **GitHub Actions** instead. It will wake up once every 15 minutes, run the poller once, and shut down.

**What to do**

Create this folder and file in your repo:

```
D:\AI\ai-customer-support\.github\workflows\poller.yml
```

Paste this:

```yaml
name: Scheduled Poller

on:
  schedule:
    - cron: '*/15 * * * *'   # runs every 15 minutes
  workflow_dispatch:          # lets you run it manually too

jobs:
  poll:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --locked --no-dev

      - name: Run poller once
        run: uv run python -c "from app.poller import poll_once; print(f'Processed {poll_once()} messages')"
        env:
          GOOGLE_CLIENT_ID: ${{ secrets.GOOGLE_CLIENT_ID }}
          GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
          GOOGLE_REFRESH_TOKEN: ${{ secrets.GOOGLE_REFRESH_TOKEN }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          POLL_INTERVAL_SECONDS: "60"
          DASHBOARD_USERNAME: "admin"
          DASHBOARD_PASSWORD: ${{ secrets.DASHBOARD_PASSWORD }}
          PYDANTIC_AI_NO_BANNER: "1"
```

**Why**

- `cron: '*/15 * * * *'` means “every 15 minutes.”
- `workflow_dispatch` adds a “Run workflow” button in GitHub so you can test it right now without waiting 15 minutes.
- `actions/checkout@v4` downloads your code onto GitHub’s server.
- `astral-sh/setup-uv@v3` installs `uv`, the fast Python package manager your project uses.
- The last step runs your poller function once and prints how many messages it processed.

**Commit and push**

```powershell
git add .github/workflows/poller.yml
git commit -m "Add scheduled poller via GitHub Actions"
git push origin main
```

---

### Step 5: Add secrets to GitHub

**What to do**

1. On GitHub, open your repository `ai-customer-support`.
2. Click **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret** and add each of these:

| Secret name | Value |
|-------------|-------|
| `GOOGLE_CLIENT_ID` | your Gmail client ID |
| `GOOGLE_CLIENT_SECRET` | your Gmail client secret |
| `GOOGLE_REFRESH_TOKEN` | your Gmail refresh token |
| `DATABASE_URL` | your Supabase connection string |
| `LLM_API_KEY` | your Gemini/LLM API key |
| `DASHBOARD_PASSWORD` | the same password you set on Render |

**Why**

GitHub Actions runs on GitHub’s servers, not your computer. It does not have access to your local `.env` file. Secrets let you pass private keys securely into the workflow so the poller can log into Gmail and Supabase.

---

### Step 6: Stop your local poller

**What to do**

If you ran the poller on your laptop earlier (from the tutorial), press **Ctrl+C** in that terminal window to stop it.

**Why**

You should never have two pollers running at the same time against the same Gmail inbox. They would both try to answer the same emails and could send duplicate replies.

---

### Step 7: Test the full flow end-to-end

**What to do**

1. **Manual trigger:** Go to GitHub → your repo → **Actions** → **Scheduled Poller** → click **Run workflow** → **Run workflow**. Wait a minute, then check the log. It should say something like `Processed 2 messages`.
2. **Send a test email:** From your personal Gmail, send an email to the demo Gmail address connected to this project.
3. **Wait up to 15 minutes** (or trigger the workflow again).
4. Check:
   - GitHub Actions log shows the message was processed.
   - A reply arrives in your personal inbox, in the same thread.
   - In Supabase, open the Table Editor → `events` table → you should see a new row.

**Why**

This proves the whole chain works: GitHub → poller → Gmail → AI → reply → Supabase.

---

### Step 8: How to update your project later

**What to do**

Whenever you change code:

```powershell
cd D:\AI\ai-customer-support
git add .
git commit -m "describe your change"
git push origin main
```

**What happens**

- **Render:** Detects the push, rebuilds the Docker image, and restarts your API automatically.
- **GitHub Actions:** The next scheduled run (or manual run) uses the new code automatically.

---

## What to skip from the original tutorial

You do **not** need any of these for the free deployment:

| Tutorial step | Why skip |
|---------------|----------|
| Hostinger VPS setup | Render hosts it for free |
| SSH keys, firewall, deploy user | Render handles servers; no SSH needed |
| Deploy key for GitHub | Render connects to GitHub directly |
| `git clone` + `nano .env` on server | Render uses dashboard environment variables |
| `docker compose up -d --build` on server | Render builds automatically from GitHub |
| Supabase IP network restrictions | Your home IP changes; rely on RLS + strong password instead |
| `git pull` on server for updates | Push to GitHub → auto-deploy |

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| Render build fails | Dockerfile error or missing `uv.lock` | Check Render deploy logs; make sure `uv.lock` is committed |
| `/health` returns error | Missing environment variable | Add all required secrets in Render dashboard |
| Poller says 0 messages processed | Gmail labels not created yet | The poller creates `ai-processed` and `needs-human` labels automatically on first run |
| No reply received | `GOOGLE_REFRESH_TOKEN` expired or wrong | Re-run the Gmail OAuth flow from Part 0 and update the secret |
| Render sleeps after inactivity | Free tier behavior | Normal. First visitor wakes it up within ~30 seconds |

---


*End of guide.*