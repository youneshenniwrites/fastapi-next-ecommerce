# app/db/init_db.py
from app.db.session import engine
from app.models.base import Base

def init_db():
    # This creates all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

if __name__ == "__main__":
    init_db()
