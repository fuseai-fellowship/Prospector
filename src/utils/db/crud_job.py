# job_crud.py
from .models.job import Job
from configs.config import logger


def save_job(session, title):
    """Create a new job or update existing job by title."""
    existing_job = session.query(Job).filter(Job.job_file_name == title).first()
    if existing_job:
        logger.info(f"Job '{title}' saved in the database")
    else:
        new_job = Job(job_file_name=title)
        session.add(new_job)
        logger.success(f"Job '{title}' added successfully.")
    session.commit()
    return session.query(Job).filter(Job.job_file_name == title).first()


def get_job(session, job_id=None, title=None):
    """Get a job by ID or title."""
    query = session.query(Job)
    if job_id is not None:
        return query.filter(Job.id == job_id).first()
    if title is not None:
        return query.filter(Job.job_file_name == title).first()
    return query.all()


def update_job(session, job_id, new_title):
    """Update job title by job ID."""
    job = session.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job with id {job_id} not found.")
        return None
    job.job_file_name = new_title
    session.commit()
    logger.info(f"Job '{job_id}' updated to '{new_title}' successfully.")
    return job


def delete_job(session, job_id):
    """Delete a job by ID."""
    job = session.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job with id {job_id} not found.")
        return False
    session.delete(job)
    session.commit()
    logger.warning(f"Job '{job.job_file_name}' deleted successfully.")
    return True
