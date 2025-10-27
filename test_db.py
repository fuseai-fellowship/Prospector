import streamlit as st
from utils.db.database import Database, User
from src.utils.file_savings import save_processed_json_resume

from sqlalchemy import create_engine
from utils.db.database import User as Base
from src.utils.db.db_instance import db

engine = create_engine("sqlite:///my_database.db")
Base.metadata.drop_all(engine)  # Drops all tables
Base.metadata.create_all(engine)  # Creates tables according to current models


# Get a session
session = db.get_session()

# Example: Add a new user
if st.button("Add Alice"):
    new_user = User(
        name="Alice",
        email="alice@example.com",
        phone_no="9812345678",
        user_resume_file_name="smth",
    )
    json_text = '{"name": "John Doe", "skills": ["Python", "Streamlit"]}'
    json_path = save_processed_json_resume(json_text, "1")
    session.add(new_user)
    session.commit()
    st.success("Added Alice!")

# Example: Show all users
users = session.query(User).all()
st.write(users)
