_fake_db= []

def save_user(user_data):
    _fake_db.append(user_data)
    return user_data

def get_all_users():
    return _fake_db