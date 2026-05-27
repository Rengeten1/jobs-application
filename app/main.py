from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import engine, Base, get_db
from app.models import Job, Config, AgentLog
from agent.orchestrator import orchestrator

load_dotenv()

# Create the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AutoJobber API")

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.applied_at.desc()).all()
    stats = {
        "total": len(jobs),
        "applied": sum(1 for j in jobs if j.status == "applied"),
        "failed": sum(1 for j in jobs if j.status == "failed"),
        "pending": sum(1 for j in jobs if j.status == "pending")
    }
    # Analytics Data
    from collections import defaultdict
    dates = defaultdict(int)
    for j in jobs:
        date_str = j.applied_at.strftime('%Y-%m-%d')
        dates[date_str] += 1
        
    chart_data = {
        "dates": list(dates.keys()),
        "counts": list(dates.values()),
        "statuses": [stats["applied"], stats["failed"], stats["pending"]]
    }
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"jobs": jobs, "stats": stats, "chart_data": chart_data}
    )

@app.get("/config", response_class=HTMLResponse)
async def get_config(request: Request, db: Session = Depends(get_db)):
    config_items = db.query(Config).all()
    config_dict = {item.key: item.value for item in config_items}
    return templates.TemplateResponse(request=request, name="config.html", context={"config": config_dict})

@app.post("/config")
async def save_config(
    request: Request,
    target_keywords: str = Form(""),
    profile_info: str = Form(""),
    db: Session = Depends(get_db)
):
    def update_config(k, v):
        item = db.query(Config).filter(Config.key == k).first()
        if not item:
            db.add(Config(key=k, value=v))
        else:
            item.value = v
            
    update_config("TARGET_KEYWORDS", target_keywords)
    update_config("PROFILE_INFO", profile_info)
    
    db.commit()
    return RedirectResponse(url="/config", status_code=303)

@app.post("/api/start")
async def start_agent():
    await orchestrator.start()
    return {"status": "started"}

@app.post("/api/stop")
async def stop_agent():
    await orchestrator.stop()
    return {"status": "stopped"}

@app.get("/api/logs")
async def get_logs(db: Session = Depends(get_db)):
    logs = db.query(AgentLog).order_by(AgentLog.timestamp.desc()).limit(50).all()
    logs.reverse()
    return [{"timestamp": log.timestamp.strftime("%H:%M:%S"), "message": log.message, "level": log.level} for log in logs]

@app.get("/api/status")
async def get_status():
    return {"running": orchestrator.running}
