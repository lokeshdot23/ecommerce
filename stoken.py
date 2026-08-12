from itsdangerous import URLSafeTimedSerializer  # type:ignore
secret_key = 'lokesh'


def entoken(data):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data, salt='extrasecurity')


def dntoken(data):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.loads(data, salt='extrasecurity', max_age=180)
