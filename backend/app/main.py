import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, products

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
    description=(
        "Portfolio ecommerce API backed by PostgreSQL. Public catalog reads use GBP "
        "decimal prices. Product writes require an active admin. Register a customer, "
        "then use Authorize with your email in the username field to obtain a bearer "
        "token. Admin bootstrap is an operator CLI, never a public endpoint. "
        "Cart, checkout and Azure deployment are planned; no real purchases are supported."
    ),
    openapi_tags=[
        {
            "name": "Health",
            "description": "Process liveness; does not check database readiness.",
        },
        {
            "name": "Products",
            "description": "Public catalog reads and admin-only product management. Prices serialize as two-place GBP strings.",
        },
        {
            "name": "auth",
            "description": "Customer registration, password login and active-user profile.",
        },
    ],
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
@app.get("/health", tags=["Health"], summary="Check API process liveness")
async def health_check() -> dict[str, str]:
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
