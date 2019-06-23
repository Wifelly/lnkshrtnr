import jwt
import datetime 
SECRET_KEY = "Hello"

def create_token(user):
    payload = {
        'sub': user['id'],
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token.decode('unicode_escape')


def parse_token(req):
    token = req.headers.get('Authorization').split()[1]
    return jwt.decode(token, SECRET_KEY, algorithms='HS256')


user = {'id' : "12"}
token = create_token(user)
print (token)