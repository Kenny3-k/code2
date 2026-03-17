from database import save_user
from email_service import send_welcome_email

def register_user(user_data):
    saved_user= save_user(user_data)
    send_welcome_email(saved_user['email'])
    return saved_user

