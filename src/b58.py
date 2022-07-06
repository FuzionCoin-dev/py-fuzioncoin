################################################################
# BASE58 ENCODING & DECODING IMPLEMENTATION
################################################################

from hashlib import sha256

CHARACTERS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def encode(s: bytes) -> bytes:
    count = 0

    for c in s:
        if c == 0:
            count += 1
        else:
            break

    num = int.from_bytes(s, 'big')
    prefix = '1' * count
    result = ''

    while num > 0:
        num, mod = divmod(num, 58)
        result = CHARACTERS[mod] + result

    return prefix + result

def encode_with_checksum(s: bytes) -> bytes:
    checksum = sha256(sha256(s).digest()).digest()[:4]
    return encode(s + checksum)

def decode(s: bytes) -> bytes:
    num = 0

    for c in s:
        num *= 58
        num += CHARACTERS.index(c)

    bc = (num.bit_length() + 7) // 8
    combined = num.to_bytes(bc, byteorder='big')

    return combined

def decode_with_checksum(s: bytes) -> bytes:
    decoded = decode(s)

    checksum = decoded[-4:]
    data = decoded[:-4]

    if sha256(sha256(data).digest()).digest()[:4] != checksum:
        raise ValueError("Bad checksum")

    return data
