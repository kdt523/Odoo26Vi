from apscheduler.schedulers.asyncio import AsyncIOScheduler

# We will initialize it with UTC timezone to prevent daylight savings issues
# It can be started/stopped during the FastAPI lifespan
scheduler = AsyncIOScheduler()
