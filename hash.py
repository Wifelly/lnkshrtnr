from hashlib import sha1
from base64 import urlsafe_b64encode


def getHash(id):
    return urlsafe_b64encode(sha1(str(id).encode()).digest()).decode()[0:12]