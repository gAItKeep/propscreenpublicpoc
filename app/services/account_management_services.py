# Standard Library imports
import datetime
import random
import uuid

# Core Flask imports
from flask import request
# from flask import jsonify

# Third-party imports
import bcrypt

# App imports
from app import db_manager as db
from ..models import User, Account, AuditLog
from ..utils import custom_errors
from ..utils.validators import AccountValidator, EmailValidator

#SI Check Import
import sys
sys.path.insert(0, '/propscreen/sicheck.py')
import propscreen.sicheck as sicheck

def api_v1_gait_llm_check_inner(prompt):
    print("ENTER api_v1_gait_llm_check_inner()")

    now = datetime.datetime.now().isoformat()

    # Returns only the response of the LLM, not the prompt so there is no 
    # innaproapiate hits during scanning output scanning
    
    llm_response = sicheck.call_to_llm(prompt)
    
    print(f"VERSION=2")
    print(f"Checking response...")
    # return the decision from sicheck
    res_prompt, res_llm_response, res_decision = sicheck.sensitive_info_check(prompt, llm_response)
    print(f"Checked response OK")

    audit_log_model = AuditLog(
        audit_log_id=str(uuid.uuid4()),
        prompt=str(res_prompt),
        llm_response=str(res_llm_response),
        decision=str(res_decision),
    )

    db.session.add(audit_log_model)
    db.session.commit()

    if res_decision == "True Positive":
        res_llm_response = "Due to your current level of access, you do not \
        have the necessary privileges to view some of the data in the response."
    http_response_body = {
        "original_prompt": prompt,
        "timestamp": now,
        "request_ip": request.remote_addr,
        "bot_response": res_llm_response
    }

    return http_response_body


def get_user_profile_from_user_model(user_model):
    user_model_dict = user_model.__dict__

    allowlisted_keys = ["username", "email"]

    for key in list(user_model_dict.keys()):
        if key not in allowlisted_keys:
            user_model_dict.pop(key)

    return user_model_dict


def update_email(current_user_model, sanitized_email):
    EmailValidator(email=sanitized_email)

    if (
        db.session.query(User.email).filter_by(email=sanitized_email).first()
        is not None
    ):
        raise custom_errors.EmailAddressAlreadyExistsError()

    current_user_model.email = sanitized_email
    db.session.add(current_user_model)

    return


def create_account(sanitized_username, sanitized_email, unhashed_password):
    AccountValidator(
        username=sanitized_username,
        email=sanitized_email,
        password=unhashed_password
    )

    if (
        db.session.query(User.email).filter_by(email=sanitized_email).first()
        is not None
    ):
        raise custom_errors.EmailAddressAlreadyExistsError()

    hash = bcrypt.hashpw(unhashed_password.encode(), bcrypt.gensalt())
    password_hash = hash.decode()

    account_model = Account()
    db.session.add(account_model)
    db.session.flush()

    user_model = User(
        username=sanitized_username,
        password_hash=password_hash,
        email=sanitized_email,
        account_id=account_model.account_id,
    )

    db.session.add(user_model)
    db.session.commit()

    return user_model


def verify_login(sanitized_email, password):
    EmailValidator(email=sanitized_email)

    user_model = db.session.query(User).filter_by(email=sanitized_email).first()

    if not user_model:
        raise custom_errors.CouldNotVerifyLogin()

    if not bcrypt.checkpw(password.encode(), user_model.password_hash.encode()):
        raise custom_errors.CouldNotVerifyLogin()

    return user_model
