# src/db/crud/user_crud.py
from typing import List, Optional, Any, Dict

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from configs.config import logger
from .models.user import User


def create_user(
    session: Session,
    *,
    name: str,
    email: str,
    phone_no: str,
    job_name: str,
    resume_file_name: Optional[str] = None,
    processed_resume_file_path: Optional[str] = None,
    interview_result_file_name: Optional[str] = None,
    interview_score: Optional[str] = None,
) -> User:
    """
    Create or update a user based on phone_no.
    If the phone_no already exists, update the existing record instead of raising IntegrityError.
    """
    try:
        # Check if a user with this phone number already exists
        existing_user = session.query(User).filter_by(phone_no=phone_no).first()

        if existing_user:
            # Update only relevant fields
            existing_user.name = name
            existing_user.email = email
            existing_user.job_name = job_name
            existing_user.resume_file_name = resume_file_name
            existing_user.processed_resume_file_name = processed_resume_file_path
            existing_user.interview_result_file_name = interview_result_file_name
            existing_user.interview_score = interview_score

            session.commit()
            session.refresh(existing_user)

            logger.info(
                "Updated existing User id=%s phone_no=%s",
                existing_user.id,
                existing_user.phone_no,
            )
            return existing_user

        # Otherwise, create a new one
        user = User(
            name=name,
            email=email,
            phone_no=phone_no,
            job_name=job_name,
            resume_file_name=resume_file_name,
            processed_resume_file_path=processed_resume_file_path,
            interview_result_file_name=interview_result_file_name,
            interview_score=interview_score,
        )

        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info("Created new User id=%s phone_no=%s", user.id, user.phone_no)
        return user

    except IntegrityError as exc:
        session.rollback()
        logger.exception(
            "Failed to create or update User (IntegrityError). email=%s phone_no=%s",
            email,
            phone_no,
        )
        raise exc


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Return user or None."""
    user = session.get(User, user_id)
    if user:
        logger.debug("Fetched User id=%s", user_id)
    else:
        logger.debug("User id=%s not found", user_id)
    return user


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """Return first user matching email or None."""
    user = session.query(User).filter(User.email == email).first()
    logger.debug("get_user_by_email(%s) -> %s", email, getattr(user, "id", None))
    return user


def get_user_by_phone(session: Session, phone_no: str) -> Optional[User]:
    """Return first user matching phone_no or None."""
    user = session.query(User).filter(User.phone_no == phone_no).first()
    logger.debug("get_user_by_phone(%s) -> %s", phone_no, getattr(user, "id", None))
    return user


def list_users(session: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    """List users with pagination (offset/limit)."""
    users = session.query(User).offset(skip).limit(limit).all()
    logger.debug("Listed users skip=%s limit=%s returned=%s", skip, limit, len(users))
    return users


def update_user(
    session: Session, user_id: int, fields: Dict[str, Any]
) -> Optional[User]:
    """
    Update user fields (only attributes that exist on the model will be set).
    Returns updated user or None if not found.
    Raises IntegrityError on unique constraint violations.
    """
    user = session.get(User, user_id)
    if not user:
        logger.warning("update_user: User id=%s not found", user_id)
        return None

    allowed_keys = {
        "name",
        "email",
        "phone_no",
        "resume_file_name",
        "processed_resume_file_path",
        "interview_result_file_name",
        "interview_score",
        "job_name",
    }

    updated = []
    for key, val in fields.items():
        if key in allowed_keys:
            setattr(user, key, val)
            updated.append(key)
        else:
            logger.debug("Ignored update field '%s' - not allowed on User", key)

    if not updated:
        logger.debug("No allowed fields to update for User id=%s", user_id)
        return user

    try:
        session.commit()
        session.refresh(user)
        logger.info("Updated User id=%s fields=%s", user_id, updated)
        return user
    except IntegrityError as exc:
        session.rollback()
        logger.exception(
            "Failed to update User id=%s (IntegrityError). fields=%s", user_id, updated
        )
        raise exc


def delete_user(session: Session, user_id: int) -> bool:
    """Delete user by id. Returns True if deleted, False if not found."""
    user = session.get(User, user_id)
    if not user:
        logger.warning("delete_user: User id=%s not found", user_id)
        return False

    try:
        session.delete(user)
        session.commit()
        logger.info("Deleted User id=%s email=%s", user_id, user.email)
        return True
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to delete User id=%s", user_id)
        raise exc
