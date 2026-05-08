from __future__ import annotations

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from askbot.config import PROJECT_ROOT, get_settings
from askbot.dashboard import router
from askbot.database import init_db
from askbot.scheduler import start_scheduler
from askbot.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    init_db()
    app.state.scheduler = start_scheduler(settings)
    yield
    # Shutdown
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)


settings = get_settings()
app = FastAPI(title="ASKBot Daily Play Store Promotion Bot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "askbot" / "static")), name="static")
app.mount("/api/images", StaticFiles(directory=str(PROJECT_ROOT / "data" / "assets")), name="images")
app.include_router(router)




def main() -> None:
    init_db()
    uvicorn.run("askbot.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()

