"""Database connection and session management for PostgreSQL.

This module handles:
- Database engine creation
- Session management with dependency injection
- Table creation and migrations
- Connection pooling and cleanup
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from src.db.models import Base
from src.utils.config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and sessions."""
    
    def __init__(self, database_url: str = None):
        """Initialize database manager with connection URL.
        
        Args:
            database_url: PostgreSQL connection string. If None, uses settings.database_url
        """
        self.database_url = database_url or settings.database_url
        
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL not configured. Please set DATABASE_URL environment variable "
                "or configure it in settings. For Railway, add PostgreSQL plugin."
            )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,  # Max 5 connections in pool
            max_overflow=10,  # Allow up to 10 overflow connections
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=settings.debug,  # Log SQL in debug mode
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Log connection info (sanitized)
        sanitized_url = self._sanitize_url(self.database_url)
        logger.info(f"Database connected: {sanitized_url}")
    
    def _sanitize_url(self, url: str) -> str:
        """Remove password from database URL for logging."""
        if "@" in url and "://" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                auth, host = rest.split("@", 1)
                if ":" in auth:
                    user, _ = auth.split(":", 1)
                    return f"{protocol}://{user}:***@{host}"
        return url
    
    def create_tables(self):
        """Create all database tables if they don't exist.
        
        This is safe to run on every startup - existing tables are not modified.
        For schema changes, use Alembic migrations.
        """
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables ready")
    
    def get_session(self) -> Session:
        """Get a new database session.
        
        Returns:
            SQLAlchemy Session object
            
        Note:
            Caller is responsible for closing the session.
            Prefer using get_db() context manager instead.
        """
        return self.SessionLocal()
    
    @contextmanager
    def get_db(self) -> Generator[Session, None, None]:
        """Context manager for database sessions.
        
        Yields:
            SQLAlchemy Session object
            
        Example:
            ```python
            with db_manager.get_db() as db:
                user = db.query(UserProfile).filter_by(id=user_id).first()
            ```
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Dispose of the database engine and close all connections."""
        logger.info("Closing database connections...")
        self.engine.dispose()


# Global database manager instance
_db_manager: DatabaseManager = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    global _db_manager
    if _db_manager is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first, "
            "or ensure it's called in main.py startup event."
        )
    return _db_manager


def init_db(database_url: str = None) -> DatabaseManager:
    """Initialize the global database manager.
    
    Args:
        database_url: Optional database URL override
        
    Returns:
        Initialized DatabaseManager instance
        
    Note:
        Call this once during application startup.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
        _db_manager.create_tables()
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.
    
    Yields:
        SQLAlchemy Session object
        
    Example:
        ```python
        @app.get("/users/{user_id}")
        def get_user(user_id: str, db: Session = Depends(get_db)):
            return db.query(UserProfile).filter_by(id=user_id).first()
        ```
    """
    db_manager = get_db_manager()
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
