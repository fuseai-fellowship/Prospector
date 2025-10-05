from typing import List, Optional
from pydantic import BaseModel, EmailStr


class PersonalDetails(BaseModel):
    name: Optional[str] = ""
    email: Optional[EmailStr] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""


class Project(BaseModel):
    title: Optional[str] = ""
    description: Optional[str] = ""


class WorkExperience(BaseModel):
    company: Optional[str] = ""
    position: Optional[str] = ""
    duration: Optional[str] = ""
    description: Optional[str] = ""


class Certification(BaseModel):
    name: Optional[str] = ""
    issuer: Optional[str] = ""
    year: Optional[str] = ""


class Education(BaseModel):
    degree: Optional[str] = ""
    institution: Optional[str] = ""
    year: Optional[str] = ""


class Others(BaseModel):
    additional_info: Optional[str] = ""


class ResumeSchema(BaseModel):
    personal_details: PersonalDetails
    projects: List[Project] = []
    work_experience: List[WorkExperience] = []
    certifications: List[Certification] = []
    education: List[Education] = []
    skills: List[str] = []
    others: Others
