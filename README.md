# AI Thumbnail Generator

> Upload a headshot. Describe your video. Get designed thumbnails in seconds.

A full-stack AI project that combines **Google Gemini**, **local image compositing**, and **real-time streaming** to generate styled YouTube-style thumbnails — built entirely on free-tier APIs.

![Demo](https://github.com/anisoni12/ai-thumbnail-generator/raw/main/demo.gif)

---

## What It Actually Does

You give it two things:
- A photo of your face
- A short description of your video topic

It gives you back two 1280×720 JPEG thumbnails, composed with gradient backgrounds, your headshot cut out and layered in, a generated title, and topic-aware badges.

No paid image generation API. No cloud GPU. Everything composited locally with Pillow.

---

## The Stack

| | |
|---|---|
| **Frontend** | React 19 · Vite · Tailwind CSS v4 · React Router |
| **Backend** | FastAPI · SQLModel · SQLite · Pydantic Settings |
| **AI — Design** | Google Gemini (titles, colors, layout, topic metadata) |
| **AI — Cutout** | rembg + ONNX Runtime (U2Net, runs locally) |
| **AI — Backgrounds** | Pollinations.ai (free, no key required) |
| **Compositing** | Pillow — all rendering done on your machine |
| **CDN** | ImageKit — hosts and serves the final output |
| **Realtime** | Server-Sent Events (SSE) — live step-by-step progress |

---

## Architecture

```
POST /api/jobs  (headshot + prompt)
        │
        ▼
FastAPI creates a Job in SQLite
        │
        ▼
Background thread runs the pipeline:
        │
        ├─ 1. Gemini → design JSON (title, colors, layout, topic_slug)
        ├─ 2. rembg → removes background from headshot locally
        ├─ 3. Pollinations.ai → fetches AI-generated background image
        └─ 4. Pillow compositor → layers everything into 1280×720 JPEG
                    └─ ImageKit → uploads final image → CDN URL
        │
        ▼
SSE stream pushes progress to frontend in real time
```

**Frontend pages:** `/` — generate · `/history` — all past jobs

---

## Pipeline in Plain English

```
"Ethical Hacking Course" + photo.jpg
        ↓
Gemini: { title: "ETHICAL HACKING", accent: "#00f2ff", layout: "headshot_right" }
        ↓
rembg cuts out the background from photo.jpg → cutout.png (runs on your CPU)
        ↓
Pollinations.ai generates a dark cinematic 1280×720 background
        ↓
Pillow layers: gradient → AI bg → glow blob → headshot cutout → title text → badges
        ↓
ImageKit hosts the JPEG → URL returned to frontend
```

---

## Compositor Templates

Six layouts, each 1280×720px, each stacking the same layers differently:

| Template | Vibe |
|---|---|
| Power Split | Headshot left, bold text right |
| Cinematic Dark | Dark overlay, centered headshot, wide title |
| Bright Pop | High contrast, saturated accent colors |
| Editorial Magazine | Text-heavy left column, portrait right |
| Neon Grid | Grid lines, glowing accent borders |
| Stacked Layers | Vertical stack, large subtitle |

Every template layers: gradient bg → AI-generated bg (blended) → topic icon watermark → headshot with glow + shadow → title → subtitle pill → topic chip

---

## Honest Note on Output Quality

The original project this was inspired by used **GPT-4o Image generation** — which produces genuinely photorealistic, high-quality AI backgrounds. That model requires a paid OpenAI API key.

This version uses **Pollinations.ai** (free, no key) + **local Pillow compositing**. The output is more template-based. It's a real architectural trade-off, not a bug.

| Component | Original | This project |
|---|---|---|
| Background gen | GPT-4o Image (paid) | Pollinations.ai (free) |
| Background removal | Cloud API | rembg / U2Net (local) |
| Design metadata | GPT-4 (paid) | Google Gemini (free tier) |

---

## Project Structure

```
ai-thumbnail-generator/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── config.py
│   ├── test_thumbnail.py
│   ├── thumbnails.db                      # SQLite database (auto-created)
│   ├── requirements.txt
│   ├── .env.example
│   └── services/
│       ├── __init__.py
│       ├── gemini_service.py
│       ├── compositor.py
│       ├── bg_removal.py
│       ├── bg_generator.py
│       ├── imagekit_service.py
│       ├── topic_illustration_service.py
│       └── unsplash_service.py            # Legacy — currently disabled
└── frontend/
    └── src/
        ├── pages/                     # Generate, History
        ├── components/                # UploadForm, ResultsGallery, ThumbnailCard
        ├── api/thumbnailApi.js        # fetch + SSE client
        └── layouts/                   # MainLayout
```

---

## Getting Started

### 1. Clone

```bash
git clone https://github.com/anisoni12/ai-thumbnail-generator.git
cd ai-thumbnail-generator
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

Fill in `backend/.env`:

```env
GEMINI_API_KEY=...
IMAGEKIT_PUBLIC_KEY=...
IMAGEKIT_PRIVATE_KEY=...
IMAGEKIT_URL_ENDPOINT=...    # https://ik.imagekit.io/yourname
HF_TOKEN=                    # Optional — HuggingFace fallback if Pollinations is down
```

```bash
uvicorn main:app --reload
# → http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env    # copy .env.example .env on Windows
npm run dev
# → http://localhost:5173
```

---

## Environment Variables

**Backend (`backend/.env`)**

| Key | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google AI Studio — design generation |
| `IMAGEKIT_PUBLIC_KEY` | Yes | ImageKit |
| `IMAGEKIT_PRIVATE_KEY` | Yes | ImageKit |
| `IMAGEKIT_URL_ENDPOINT` | Yes | Your ImageKit URL endpoint |
| `HF_TOKEN` | No | HuggingFace fallback background gen |

**Frontend (`frontend/.env`)**

| Key | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend URL |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/jobs` | Create job — multipart: `headshot`, `prompt`, `style_count` |
| `GET` | `/api/jobs` | List all jobs |
| `GET` | `/api/jobs/{id}` | Get single job |
| `GET` | `/api/jobs/{id}/thumbnails` | Get job results |
| `GET` | `/api/jobs/{id}/stream` | SSE live progress stream |
| `DELETE` | `/api/jobs` | Clear all history |

**SSE Events**

```
event: job_started      data: {"job_id": 1}
event: step_progress    data: {"step": "Removing background..."}
event: job_completed    data: {"job_id": 1, "thumbnails": [...]}
event: job_failed       data: {"job_id": 1, "error": "..."}
```

---

## Roadmap

- [ ] True AI background generation via fal.ai / Stable Diffusion (waiting on a stable free tier)
- [ ] Drag-to-reposition headshot after generation
- [ ] Multi-format export — 1080p, vertical Shorts
- [ ] Per-user accounts with rate limiting

---

## Inspiration

Built after watching [Hitesh Choudhary's FastAPI + AI project walkthrough](https://www.youtube.com/watch?v=EB5_nETqdx0). I didn't follow along — I watched the architecture breakdown, closed the video, and built my own version from scratch with free alternatives. The idea of a full end-to-end AI pipeline from upload to CDN-hosted output was the interesting part.

---

## License

MIT
