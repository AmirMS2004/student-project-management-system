import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .reminders import reminder_loop
from .routers import (
    admin,
    auth,
    calendar,
    dashboard,
    files,
    grades,
    meetings,
    messages,
    notifications,
    projects,
    reports,
    requests,
    users,
)

# Database schema is managed by Alembic migrations, not created here.
# Run `alembic upgrade head` (from backend/) before starting the server.


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Periodically scans for calendar events (meetings, defense dates, weekly
    # report deadlines) happening in the next 24h and notifies the relevant
    # users. Only runs for the real server process, not the test suite (the
    # plain TestClient used in tests never triggers lifespan/startup — tests
    # call check_and_send_reminders() directly with their own session).
    task = asyncio.create_task(reminder_loop())
    yield
    task.cancel()


app = FastAPI(title="سامانه مدیریت پروژه‌های دانشجویی", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(requests.router)
app.include_router(meetings.router)
app.include_router(reports.router)
app.include_router(grades.router)
app.include_router(files.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(calendar.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
