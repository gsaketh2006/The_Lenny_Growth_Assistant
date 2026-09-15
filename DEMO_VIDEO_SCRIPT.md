# Demo Video Script & Walkthrough (2–3 Minutes)
# Project: The Lenny Growth Assistant
**Presenter:** Forward Deployed Engineer (FDE)  
**Target Audience:** Technical Evaluation Committee / Product Reviewers  
**Duration:** ~2 minutes 45 seconds  

---

## 🎬 Section 1: Problem & Hook (0:00 – 0:35)

- **[Camera On / Face-to-Camera]**
  > *"Hi everyone, I'm presenting **The Lenny Growth Assistant**—an enterprise-grade, full-stack conversational intelligence platform strictly grounded in over 300 episode transcripts from Lenny's Podcast and Newsletter archive.*
  > 
  > *General-purpose LLMs hallucinate vague advice when asked high-stakes product questions. Operators don't need generic summaries; they need battle-tested frameworks from proven leaders like Brian Balfour, Elena Verna, and Shreyas Doshi—with verifiable citations and executable outputs.*
  > 
  > *Let's jump directly into the live demo running 100% locally on Ollama."*

---

## 💻 Section 2: Product Walkthrough & Local Ollama Execution (0:35 – 1:30)

- **[Screen Share: Application Workspace at `http://localhost:3000` with Ollama selected in the sidebar]**
  > *"Notice first in the sidebar that we are running on **Ollama Local** with zero cloud API keys configured.*
  > 
  > *Let's ask a strategic question: **'What did Brian Balfour say about growth loops vs funnels?'**"*
  > 
  > *[Show real-time token streaming]*
  > 
  > *"Notice three things immediately:*
  > 1. *The **Grounding Confidence Indicator** at the top displays **High Grounding (88%)** based on mathematical retrieval density.*
  > 2. *Clicking the **Sources Pill** opens our interactive **Citation Inspector**, displaying exact episode titles, guest names, similarity match percentages, and verbatim quotes.*
  > 3. *The answer quotes Brian verbatim and provides bracketed citation tokens."*

---

## 🧪 Section 3: The Unique Differentiator — Growth Experiment Card & Refusal Guardrail (1:30 – 2:15)

- **[Screen Share: Triggering Skill 3 & Insufficient Grounding]**
  > *"Now let's see our first key differentiator: **The Growth Experiment Card Generator**.*
  > 
  > *Let's say: **'Turn Elena Verna's B2B PLG advice into a 1-week growth experiment.'**"*
  > 
  > *[Show Router log in message pill + Artifact Viewer mounting]*
  > 
  > *"The intelligent 3-Skill Router logs its exact rationale and dispatches to Skill 3. Look at the **Artifact Viewer** beside the chat: it live-renders a dedicated Growth Experiment Card with:*
  > - *A strict **Hypothesis** (`If [Action], then [Outcome], because [Mechanism]`)*
  > - *A primary **Target Metric** badge*
  > - *A **1-Week Sprint Execution Timeline** (`Day 1-2`, `Day 3-4`, `Day 5-7`)*
  > - *An **Invalidation & Risk Matrix***
  > - *And 1-click **Copy Markdown / JSON** export buttons.*
  > 
  > *Next, let's test what happens when we ask something outside Lenny's podcast, like: **'How do I bake sourdough bread?'**"*
  > 
  > *[Show Red Insufficient Grounding Banner]*
  > 
  > *"Instead of hallucinating or guessing, the Grounding Confidence system triggers an explicit **Insufficient Grounding Refusal Guardrail**, telling the user honestly that the topic is not covered in the archive."*

---

## ⚙️ Section 4: Technical Architecture & Real Trade-off (2:15 – 2:45)

- **[Screen Share / Face-to-Camera]**
  > *"Behind the scenes, we built this on FastAPI, async PostgreSQL with pgvector, and a React + Tailwind frontend.*
  > 
  > *For security, all untrusted HTML and dynamic CSS in the Artifact Viewer are strictly isolated inside an `<iframe>` with `sandbox="allow-scripts"` and no `allow-same-origin`, preventing parent DOM access, cookie leakage, and XSS attacks.*
  > 
  > *One key architectural trade-off we made was using **Server-Sent Events (SSE)** over WebSockets: SSE gave us lightweight, one-way multiplexed streaming for tokens, routing rationales, confidence badges, and live artifact events with zero WebSocket reconnection state complexity.*
  > 
  > *The entire system launches with a single `docker compose up --build` command and passes 10 out of 10 automated unit and integration tests.*
  > 
  > *Thank you, and enjoy exploring The Lenny Growth Assistant!"*
