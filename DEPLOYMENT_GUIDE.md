# Deployment Guide: Render (Backend) + Vercel (Frontend)

This guide provides end-to-end instructions for deploying **The Lenny Growth Assistant** to production with:
- **Backend API:** [Render](https://render.com) (FastAPI + RAG Engine + SSE Streaming)
- **Frontend SPA:** [Vercel](https://vercel.com) (React 18 + Vite + Tailwind CSS + Artifact Sandbox)
- **Persistence:** [Supabase](https://supabase.com) (Cloud PostgreSQL database)

---

## Architecture at a Glance

`
[ Browser / User ]
       |
       | HTTPS
       v
[ Vercel CDN (Frontend) ]
  https://lenny-growth-assistant.vercel.app
       |
       | REST API + SSE Streams
       v
[ Render Web Service (Backend) ]
  https://lenny-growth-backend.onrender.com
       |
       +---> [ Supabase PostgreSQL (Users, Sessions, Messages, Artifacts) ]
       +---> [ Cloud LLMs: Groq / Anthropic / OpenAI / DeepSeek / Custom ]
`

---

## Part 1: Push Repository to GitHub

Ensure your latest local changes are pushed to your GitHub repository:

`ash
git add .
git commit -m "Configure Render and Vercel cloud deployment"
git push origin main
`

---

## Part 2: Deploy Backend to Render

### Option A: 1-Click Blueprint (Recommended)
1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect [ender.yaml](./render.yaml).
5. In the environment variable prompts, set your DATABASE_URL (Supabase connection string) and optional LLM keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY).
6. Click **Apply**.

### Option B: Manual Web Service Setup
1. In the Render Dashboard, click **New +** -> **Web Service**.
2. Select your GitHub repository.
3. Configure the following fields:
   - **Name:** lenny-growth-assistant-backend
   - **Language / Runtime:** Python 3
   - **Root Directory:** . *(leave blank or set to dot)*
   - **Build Command:** pip install -r backend/requirements.txt
   - **Start Command:** uvicorn backend.app.main:app --host 0.0.0.0 --port 
4. In the **Environment Variables** section, add:
   - PYTHON_VERSION = 3.12.4
   - ENVIRONMENT = production
   - DATABASE_URL = postgresql+asyncpg://postgres:YOUR_PASSWORD@db.djlpkmafgttemljmrcvb.supabase.co:5432/postgres
   - GROQ_API_KEY = your_groq_api_key *(optional)*
   - ANTHROPIC_API_KEY = your_anthropic_api_key *(optional)*
   - OPENAI_API_KEY = your_openai_api_key *(optional)*
5. Click **Deploy Web Service**.
6. Once deployed, note down your Render service URL (e.g., https://lenny-growth-assistant-backend.onrender.com).
7. Verify it is running by opening https://<your-render-url>/api/health in your browser.

---

## Part 3: Deploy Frontend to Vercel

1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** -> **Project**.
3. Select your GitHub repository and click **Import**.
4. In the **Configure Project** settings:
   - **Framework Preset:** Vite
   - **Root Directory:** Click **Edit** and choose rontend *(or leave root; both ercel.json configurations are included)*.
   - **Build Command:** 
pm run build
   - **Output Directory:** dist
5. Under **Environment Variables**, add:
   - **Key:** VITE_API_URL
   - **Value:** https://<your-render-url>/api *(replace with your actual Render backend URL)*
6. Click **Deploy**.
7. Vercel will build and launch your production web app in ~1 minute.

---

## Part 4: Production Verification Checklist

1. **Authentication:**
   - Open your Vercel URL.
   - Register a new account or log in with your credentials.
   - Verify that your user session persists across browser refreshes.

2. **Model Engine Selection:**
   - Open the **LLM Engine** settings in the top right.
   - Choose a cloud model (Groq LLaMA 3.3 70B, Claude 3.5 Sonnet, or OpenAI GPT-4o) or add a custom OpenAI-compatible endpoint.
   - Run the connection test.

3. **Grounded Q&A & Streaming:**
   - Ask: *"What are the 3 core growth engines according to Brian Balfour?"*
   - Verify real-time token streaming and verifiable podcast citations with timestamps and episode links.

4. **Ship 30 for 30 & Growth Artifacts:**
   - Ask: *"Create a Ship 30 for 30 essay on product-market fit."*
   - Ask: *"Generate a growth experiment card for onboarding activation."*
   - Verify the interactive Sandboxed Artifact Viewer renders the interactive HTML card cleanly.
