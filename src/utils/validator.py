import streamlit as st
import re
import os
from typing import Tuple, List


class Validator:
    """Validates all fields in the application form, including resume."""

    # -----------------------------
    # Constants
    # -----------------------------
    ALLOWED_TYPES = {
        "application/pdf": [".pdf"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
            ".docx"
        ],
        "application/msword": [".doc"],
    }
    MAX_SIZE_MB = 5
    EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    PHONE_PATTERN = r"^9\d{9}$"  # Must start with 9 and have total 10 digits

    # -----------------------------
    # Main validation
    # -----------------------------
    def validate(self, name: str, email: str, phone: str) -> Tuple[bool, List[str]]:
        """Validates all text fields and returns (is_valid, errors_list)."""
        errors = []

        # --- Basic text fields ---
        if not name.strip():
            errors.append("Full name is required.")

        if not email.strip():
            errors.append("Email is required.")
        elif not self._is_valid_email(email):
            errors.append("Invalid email format.")

        if phone.strip() and not self._is_valid_phone(phone):
            errors.append(
                "Invalid phone number. Must start with 9 and be exactly 10 digits."
            )

        return (len(errors) == 0, errors)

    # -----------------------------
    # Resume validation
    # -----------------------------
    def validate_resume(self, resume_file) -> Tuple[bool, str]:
        """Validates resume file for type, extension, and size."""
        if not resume_file:
            return False, "Resume upload is required."

        # --- File metadata ---
        file_type = getattr(resume_file, "type", "")
        file_name = getattr(resume_file, "name", "")
        file_ext = os.path.splitext(file_name)[-1].lower()

        # --- Type / extension check ---
        allowed_extensions = sum(self.ALLOWED_TYPES.values(), [])
        if file_type not in self.ALLOWED_TYPES and file_ext not in allowed_extensions:
            return False, "Invalid file type. Allowed: PDF, DOC, DOCX."

        # --- Size check ---
        try:
            resume_file.seek(0, os.SEEK_END)
            size_mb = resume_file.tell() / (1024 * 1024)
            resume_file.seek(0)
        except Exception:
            return False, "Could not determine file size. Please re-upload."

        if size_mb > self.MAX_SIZE_MB:
            return (
                False,
                f"File too large ({size_mb:.1f} MB). Max allowed: {self.MAX_SIZE_MB} MB.",
            )

        return True, "Resume is valid."

    # -----------------------------
    # Helper methods
    # -----------------------------
    def _is_valid_email(self, email: str) -> bool:
        """Validates email using regex."""
        return re.match(self.EMAIL_PATTERN, email) is not None

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format (must start with 9 and have 10 digits)."""
        return re.match(self.PHONE_PATTERN, phone) is not None
