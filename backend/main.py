import asyncio
import json
import traceback
from fastapi import FastAPI, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from contextlib import asynccontextmanager

from database import create_db_and_tables, get_db
from models import Job, Thumbnail
from services.imagekit_service import upload_headshot
from services.gemini_service import get_thumbnail_designs
from services.compositor import compose_thumbnail
from services.bg_generator import fetch_background, style_for_template
from services.unsplash_service import get_background_image
from services.bg_removal import remove_background
from services.topic_illustration_service import fetch_illustration

job_subscribers = {}
job_events = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Warm up the rembg model so the first job isn't slow (also downloads on first ever run)
    try:
        import threading
        from services.bg_removal import _ensure_session
        threading.Thread(target=_ensure_session, daemon=True).start()
        print("[startup] bg_removal model warm-up scheduled")
    except Exception as e:
        print(f"[startup] bg_removal warm-up skipped: {e}")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def notify_subscribers_sync(job_id: int, event_type: str, data: dict, loop: asyncio.AbstractEventLoop):
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    if job_id not in job_events:
        job_events[job_id] = []
    job_events[job_id].append(message)
    
    if job_id in job_subscribers:
        for queue in job_subscribers[job_id]:
            asyncio.run_coroutine_threadsafe(queue.put(message), loop)

def process_thumbnail_job_sync(
    job_id: int,
    headshot_content: bytes,
    filename: str,
    prompt: str,
    style_count: int,
    db: Session,
    loop: asyncio.AbstractEventLoop
):
    try:
        job = db.get(Job, job_id)
        if not job:
            return

        job.status = "processing"
        db.add(job)
        db.commit()

        notify_subscribers_sync(job_id, "job_started", {"job_id": job_id}, loop)

        # STEP 1 — Gemini designs
        notify_subscribers_sync(job_id, "step_progress", {"step": "Generating designs with Gemini..."}, loop)
        designs = get_thumbnail_designs(prompt, style_count)

        # STEP 2 — Upload original headshot to ImageKit (for storage)
        notify_subscribers_sync(job_id, "step_progress", {"step": "Uploading headshot..."}, loop)
        upload_headshot(headshot_content, filename)

        # STEP 2b — Remove background once (reused across all variants)
        notify_subscribers_sync(job_id, "step_progress", {"step": "Removing background with AI..."}, loop)
        cutout_bytes = remove_background(headshot_content)
        headshot_for_compose = cutout_bytes or headshot_content

        # STEP 2c — Fetch topic illustration once (same icon across variants)
        notify_subscribers_sync(job_id, "step_progress", {"step": "Finding topic illustration..."}, loop)
        topic_slug_hint = (designs[0].get("topic_slug") if designs else "") or prompt
        illustration_bytes = fetch_illustration(topic_slug_hint)
        if illustration_bytes:
            print(f"[main] illustration fetched ({len(illustration_bytes)} bytes) for '{topic_slug_hint}'")
        else:
            print(f"[main] no illustration for '{topic_slug_hint}'")

        # STEP 3 — Composite each design
        thumbnails_data = []
        for i, design in enumerate(designs):
            style_name = design.get("style_name", f"Style {i+1}")
            fal_prompt = design.get("fal_prompt", f"YouTube thumbnail, {prompt}, cinematic lighting, 8K, photorealistic")

            notify_subscribers_sync(
                job_id,
                "step_progress",
                {"step": f"Composing {style_name} ({i+1}/{len(designs)})..."},
                loop
            )

            bg_image_bytes = None
            unsplash_query = design.get("unsplash_query", "").strip()
            if unsplash_query:
                bg_image_bytes = get_background_image(unsplash_query)

            # Try AI background if unsplash didn't return anything
            if not bg_image_bytes:
                bg_image_bytes = fetch_background(
                    style=style_for_template(i),
                    topic=design.get("title", prompt),
                    accent_color=design.get("accent_color", "#7c3aed"),
                    seed=job_id * 10 + i
                )

            final_image_bytes = compose_thumbnail(
                headshot_bytes=headshot_for_compose,
                bg_image_bytes=bg_image_bytes,
                design=design,
                prompt_text=prompt,
                headshot_is_cutout=cutout_bytes is not None,
                illustration_bytes=illustration_bytes,
                template_index=i,
            )

            # Upload to ImageKit
            composed_filename = f"thumb_{job_id}_{i+1}.jpg"
            final_url = upload_headshot(final_image_bytes, composed_filename)

            thumbnail = Thumbnail(
                job_id=job_id,
                title=design.get("title", "Thumbnail"),
                prompt_used=design.get("fal_prompt", prompt),
                image_url=final_url
            )
            db.add(thumbnail)
            db.commit()
            db.refresh(thumbnail)

            thumbnails_data.append({
                "id": thumbnail.id,
                "title": thumbnail.title,
                "image_url": thumbnail.image_url
            })
        # Finalize job
        job.status = "completed"
        db.add(job)
        db.commit()

        notify_subscribers_sync(
            job_id,
            "job_completed",
            {"job_id": job_id, "thumbnails": thumbnails_data},
            loop
        )

    except Exception as e:
        print(f"Job {job_id} failed:")
        traceback.print_exc()

        job = db.get(Job, job_id)
        if job:
            job.status = "failed"
            db.add(job)
            db.commit()

        notify_subscribers_sync(
            job_id,
            "job_failed",
            {"job_id": job_id, "error": str(e)},
            loop
        )

@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    style_count: int = Form(...),
    headshot: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    if style_count < 1 or style_count > 3:
        raise HTTPException(status_code=400, detail="Style count must be between 1 and 3")
    if not headshot.content_type or not headshot.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file")

    job = Job(prompt=prompt, style_count=style_count)
    db.add(job)
    db.commit()
    db.refresh(job)

    content = await headshot.read()

    loop = asyncio.get_running_loop()
    from database import engine
    def run_bg_task():
        with Session(engine) as bg_session:
            process_thumbnail_job_sync(
                job.id, content, headshot.filename,
                prompt, style_count, bg_session, loop
            )

    background_tasks.add_task(run_bg_task)
    return {"job_id": job.id, "status": job.status}

@app.get("/api/jobs/{job_id}/stream")
async def stream_job_updates(job_id: int):
    if job_id not in job_subscribers:
        job_subscribers[job_id] = []

    queue = asyncio.Queue()
    job_subscribers[job_id].append(queue)

    async def event_generator():
        try:
            for msg in job_events.get(job_id, []):
                yield msg
            while True:
                yield await queue.get()
        except asyncio.CancelledError:
            job_subscribers[job_id].remove(queue)
            if not job_subscribers[job_id]:
                del job_subscribers[job_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/jobs/{job_id}/thumbnails")
def get_job_thumbnails(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.thumbnails

@app.delete("/api/jobs")
def clear_all_jobs(db: Session = Depends(get_db)):
    thumbnails = db.exec(select(Thumbnail)).all()
    for t in thumbnails:
        db.delete(t)
    jobs = db.exec(select(Job)).all()
    for j in jobs:
        db.delete(j)
    db.commit()
    return {"deleted": True}

@app.get("/api/jobs")
def get_all_jobs(db: Session = Depends(get_db)):
    jobs = db.exec(select(Job).order_by(Job.id.desc())).all()
    return [
        {
            "id": job.id,
            "prompt": job.prompt,
            "status": job.status,
            "created_at": job.created_at,
            "thumbnails": [
                {"id": t.id, "title": t.title, "prompt_used": t.prompt_used, "image_url": t.image_url}
                for t in job.thumbnails
            ]
        }
        for job in jobs
    ]