# src/db/__init__.py
from .database import Database, db
from .models.user import User
from .models.job import Job
from .crud_job import save_job, get_job, delete_job, update_job
from .crud_user import (
    create_user,
    delete_user,
    update_user,
    get_user_by_id,
    get_user_by_email,
    get_user_by_phone,
    list_users,
)
