# src/db/database.py
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from configs.config import settings
from .base import Base
from .models.user import User
from .models.job import Job


class Database:
    _instance = None  # Singleton instance

    def __new__(cls, db_url=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(db_url)
        return cls._instance

    def _init(self, db_url=None):
        if db_url is None:
            db_url = settings.get("db_url")
        self.engine = create_engine(db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self._ensure_tables()

    def _ensure_tables(self):
        """Create tables if they don't exist"""
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        if "users" not in table_names or "jobs" not in table_names:
            Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get a new session"""
        return self.Session()


db = Database()  # only one instance, safe across reruns
