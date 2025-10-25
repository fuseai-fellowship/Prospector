import json
from ...schemas.resume_schema import ResumeSchema
from ...utils.validator import Validator
from .render_final_application import render_final_application
import streamlit as st


def render_application_info(
    resume_path: str, application_controller
) -> ResumeSchema | None:
    """
    Render editable resume info using Pydantic models.
    Returns a ResumeSchema if the user clicks Save; otherwise returns None.
    """
    # Load existing application info as Pydantic model
    application_info = application_controller.process_applicant_info(
        resume_file_path=resume_path
    )
    validator = Validator()
    st.markdown("### Check for Your Informaion")
    st.write(
        "Review the information extracted from your CV and correct any inaccuracies. To add new entries, paste a JSON array into the corresponding 'New ... (JSON)' field."
    )

    with st.form("edit_resume_form"):
        # --- Personal details ---
        pd = application_info.personal_details
        st.subheader("Personal details")
        name = st.text_input("Name", value=pd.name)
        email = st.text_input("Email", value=pd.email)
        phone = st.text_input("Phone", value=pd.phone)
        address = st.text_input("Address", value=pd.address)
        linkedin = st.text_input("LinkedIn URL", value=pd.linkedin)
        github = st.text_input("GitHub URL", value=pd.github)

        # --- Projects ---
        st.subheader("Projects (existing)")
        projects = application_info.projects or []
        new_projects_inputs = []
        for i, proj in enumerate(projects):
            st.markdown(f"**Project #{i + 1}**")
            t = st.text_input(
                f"Project title #{i + 1}", value=proj.title, key=f"proj_title_{i}"
            )
            d = st.text_area(
                f"Project description #{i + 1}",
                value=proj.description,
                key=f"proj_desc_{i}",
            )
            new_projects_inputs.append(type(proj)(title=t, description=d))
        st.caption(
            'Append new projects as JSON array: [{"title":"T1","description":"D1"}, ...]'
        )
        new_projects_json = st.text_area("New projects (JSON)", value="", height=80)

        # --- Work experience ---
        st.subheader("Work experience (existing)")
        work_ex = application_info.work_experience or []
        new_work_inputs = []
        for i, w in enumerate(work_ex):
            st.markdown(f"**Work #{i + 1}**")
            company = st.text_input(
                f"Company #{i + 1}", value=w.company, key=f"we_company_{i}"
            )
            position = st.text_input(
                f"Position #{i + 1}", value=w.position, key=f"we_position_{i}"
            )
            duration = st.text_input(
                f"Duration #{i + 1}", value=w.duration, key=f"we_duration_{i}"
            )
            desc = st.text_area(
                f"Description #{i + 1}", value=w.description, key=f"we_desc_{i}"
            )
            new_work_inputs.append(
                type(w)(
                    company=company,
                    position=position,
                    duration=duration,
                    description=desc,
                )
            )
        st.caption("Append new work items as JSON array.")
        new_work_json = st.text_area("New work_experience (JSON)", value="", height=80)

        # --- Certifications ---
        st.subheader("Certifications")
        certs = application_info.certifications or []
        new_certs_inputs = []
        for i, c in enumerate(certs):
            name_c = st.text_input(
                f"Cert name #{i + 1}", value=c.name, key=f"cert_name_{i}"
            )
            issuer = st.text_input(
                f"Issuer #{i + 1}", value=c.issuer, key=f"cert_issuer_{i}"
            )
            year = st.text_input(f"Year #{i + 1}", value=c.year, key=f"cert_year_{i}")
            new_certs_inputs.append(type(c)(name=name_c, issuer=issuer, year=year))
        st.caption("Append new certifications as JSON array.")
        new_certs_json = st.text_area("New certifications (JSON)", value="", height=80)

        # --- Education ---
        st.subheader("Education")
        education = application_info.education or []
        new_edu_inputs = []
        for i, e in enumerate(education):
            degree = st.text_input(
                f"Degree #{i + 1}", value=e.degree, key=f"edu_degree_{i}"
            )
            inst = st.text_input(
                f"Institution #{i + 1}", value=e.institution, key=f"edu_inst_{i}"
            )
            year_e = st.text_input(f"Year #{i + 1}", value=e.year, key=f"edu_year_{i}")
            new_edu_inputs.append(type(e)(degree=degree, institution=inst, year=year_e))
        st.caption("Append new education items as JSON array.")
        new_edu_json = st.text_area("New education (JSON)", value="", height=80)

        # --- Skills ---
        st.subheader("Skills")
        skills = application_info.skills or []
        skills_input = st.text_input(
            "Skills (comma-separated)", value=", ".join(skills)
        )

        # --- Others ---
        st.subheader("Other / Additional info")
        others = application_info.others
        others_input = st.text_area("Additional info", value=others.additional_info)

        submit = st.form_submit_button("Save changes")

    if submit:
        # Helper to parse JSON arrays into the correct Pydantic type
        is_valid, errors = validator.validate(name=name, email=email, phone=phone)
        if not is_valid:
            for err in errors:
                st.error(err)
        else:

            def parse_json_list(text, cls):
                if not text.strip():
                    return []
                data = json.loads(text)
                return [cls(**item) for item in data if isinstance(item, dict)]

            projects += parse_json_list(
                new_projects_json,
                type(projects[0]) if projects else type(new_projects_inputs[0]),
            )
            work_ex += parse_json_list(
                new_work_json, type(work_ex[0]) if work_ex else type(new_work_inputs[0])
            )
            certs += parse_json_list(
                new_certs_json, type(certs[0]) if certs else type(new_certs_inputs[0])
            )
            education += parse_json_list(
                new_edu_json,
                type(education[0]) if education else type(new_edu_inputs[0]),
            )

            # Return updated ResumeSchema
            updated_info = type(application_info)(
                personal_details=type(pd)(
                    name=name.strip(),
                    email=email.strip(),
                    phone=phone.strip(),
                    address=address.strip(),
                    linkedin=linkedin.strip(),
                    github=github.strip(),
                ),
                projects=projects,
                work_experience=work_ex,
                certifications=certs,
                education=education,
                skills=[
                    s.strip() for s in (skills_input or "").split(",") if s.strip()
                ],
                others=type(others)(additional_info=(others_input or "").strip()),
            )
            print(updated_info)

            render_final_application(updated_info=updated_info, st=st)
    return None
