import random
import string


def genotp():
    characters = string.ascii_letters + string.digits + string.punctuation
    otp = ''.join(random.choice(characters) for _ in range(6))
    return otp
