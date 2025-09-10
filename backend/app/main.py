from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import structlog
from app.api.v1 import products, auth

# --------------------------
# Logging Configuration
# --------------------------
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# --------------------------
# App Initialization
# --------------------------
app = FastAPI(
    title="E-Commerce API",
    description="Backend API for E-Commerce App (FastAPI + PostgreSQL + Redis + AWS-ready)",
    version="0.1.0",
)

# --------------------------
# CORS Middleware
# --------------------------
origins = [
    "http://localhost:3000",  # Next.js dev frontend
    "http://127.0.0.1:3000",
    # Add your production frontend domain here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Health Check Endpoint
# --------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    Returns "OK" if the API is running.
    """
    logger.info("Health check requested")
    return {"status": "ok"}

# --------------------------
# Placeholder for Routers
# --------------------------
# from app.api.v1 import products, users
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
