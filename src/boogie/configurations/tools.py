import base64
from hashlib import md5


def secret_hash(data):
    strings = []
    for key, value in sorted(data.items()):
        strings.append(key)
        try:
            data = hash(value)
            if data != -1:
                strings.append(str(data))
        except TypeError:
            pass
    print(strings)
    data = ''.join(strings)
    hash_value = md5(data.encode('utf8')).digest()
    return base64.b85encode(hash_value).decode('ascii')
