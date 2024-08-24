from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.logs.logger_config import log
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# Create the database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Allow fastAPI to use the database via this function
def get_db():
    db = SessionLocal()
    try:
        yield db # Access db (dependency injection)
    except Exception as e:
        log(f"Error in database connection - {str(e)}")
    finally:
        db.close()