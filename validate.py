from passlib.hash import pbkdf2_sha256
from db_wrapper import request_db

db = request_db('db.db')


def validate_access(login, cell, value):
    owner = db.request_select('user_id', 'Urls', cell, value)
    if owner[0][0] == login:
        return True
    else:
        return False
