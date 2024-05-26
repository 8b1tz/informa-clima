from fastapi import FastAPI

from src.routers import locations

app = FastAPI()

app.include_router(locations.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
