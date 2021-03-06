import hashlib
import hmac
from io import BytesIO

class FieldElement:
    def __init__(self, num: int, prime: int):
        if num >= prime or num < 0:
            raise ValueError(f"Number is out of range between 0 and {prime - 1}")

        self.num = num
        self.prime = prime

    def __repr__(self) -> str:
        return f"FieldElement_{self.prime}({self.num})"

    def __eq__(self, other) -> bool:
        if other is None:
            return False

        return (self.num == other.num) and (self.prime == other.prime)

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __add__(self, other):
        if self.prime != other.prime:
            raise TypeError("Cannot add two numbers from different elements")

        num = (self.num + other.num) % self.prime
        return self.__class__(num, self.prime)

    def __sub__(self, other):
        if self.prime != other.prime:
            raise TypeError("Cannot subtract two numbers from different elements")

        num = (self.num - other.num) % self.prime
        return self.__class__(num, self.prime)

    def __mul__(self, other):
        if self.prime != other.prime:
            raise TypeError("Cannot multiply two numbers from different elements")

        num = (self.num * other.num) % self.prime
        return self.__class__(num, self.prime)

    def __pow__(self, exponent: int):
        n = exponent % (self.prime - 1)
        num = pow(self.num, n, self.prime)

        return self.__class__(num, self.prime)

    def __truediv__(self, other):
        if self.prime != other.prime:
            raise TypeError("Cannot divide two numbers from different elements")

        num = (self.num * pow(other.num, self.prime - 2, self.prime)) % self.prime
        return self.__class__(num, self.prime)

    def __rmul__(self, coefficient: int):
        num = (self.num * coefficient) % self.prime
        return self.__class__(num=num, prime=self.prime)

class Point:
    def __init__(self, x, y, a, b):
        self.x = x
        self.y = y
        self.a = a
        self.b = b

        if self.x is None and self.y is None:
            return

        if self.y ** 2 != (self.x ** 3 + a * x + b):
            raise ValueError(f"The point ({x}, {y}) is not on the curve")

    def __eq__(self, other) -> bool:
        return (self.x == other.x) and (self.y == other.y) and (self.a == other.a) and (self.b == other.b)

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __repr__(self) -> str:
        if self.x is None:
            return "Point(infinity)"

        if isinstance(self.x, FieldElement):
            return f"Point({self.x.num},{self.y.num})_{self.a.num}_{self.b.num} FieldElement({self.x.prime})"

        return f"Point({self.x},{self.y})_{self.a}_{self.b}"

    def __add__(self, other):
        if self.a != other.a or self.b != other.b:
            raise TypeError(f"The points {self}, {other} are not on the same curve")

        if self.x is None:
            return other

        if other.x is None:
            return self

        if self.x == other.x and self.y != other.y:
            return self.__class__(None, None, self.a, self.b)

        if self.x != other.x:
            s = (other.y - self.y) / (other.x - self.x)
            x = s**2 - self.x - other.x
            y = s * (self.x - x) - self.y

            return self.__class__(x, y, self.a, self.b)

        if self == other and self.y == 0 * self.x:
            return self.__class__(None, None, self.a, self.b)

        if self == other:
            s = (3 * self.x**2 + self.a) / (2 * self.y)
            x = s**2 - 2 * self.x
            y = s * (self.x - x) - self.y

            return self.__class__(x, y, self.a, self.b)

    def __rmul__(self, coefficient: int):
        coef = coefficient
        current = self
        result = self.__class__(None, None, self.a, self.b)

        while coef:
            if coef & 1:
                result += current
            current += current
            coef >>= 1
        return result

################################################################
# SECP256K1 & ECDSA implementation
################################################################

S256_PRIME = 2**256 - 2**32 - 977
S256_CURVE_A = 0
S256_CURVE_B = 7
S256_N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141

class S256Field(FieldElement):
    def __init__(self, num: int, prime: int = None):
        super().__init__(num = num, prime=S256_PRIME)

    def sqrt(self):
        return self ** ((S256_PRIME + 1) // 4)

    def __repr__(self) -> str:
        return "S256Field({:x})".format(self.num).zfill(64)

class S256Point(Point):
    def __init__(self, x, y, a = None, b = None):
        a = S256Field(S256_CURVE_A)
        b = S256Field(S256_CURVE_B)

        if type(x) == int:
            super().__init__(x=S256Field(x), y=S256Field(y), a=a, b=b)
        else:
            super().__init__(x=x, y=y, a=a, b=b)

    def __repr__(self) -> str:
        if self.x is None:
            return "S256Point(infinity)"

        return f"S256Point({self.x}, {self.y})"

    def __rmul__(self, coefficient: int):
        coef = coefficient % S256_N
        return super().__rmul__(coef)

    def verify(self, z, sig) -> bool:
        s_inv = pow(sig.s, S256_N - 2, S256_N)
        u = z * s_inv % S256_N
        v = sig.r * s_inv % S256_N
        total = u * S256_G + v * self

        return total.x.num == sig.r

S256_G = S256Point(
    0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
    0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
)

class Signature:
    def __init__(self, r, s):
        self.r = r
        self.s = s

    def __repr__(self) -> str:
        return f"Signature(r={self.r}, s={self.s})"

class PrivateKey:
    def __init__(self, secret):
        self.secret = secret
        self.point = secret * S256_G

    def hex(self) -> str:
        return "{:x}".format(self.secret).zfill(64)

    def sign(self, z: int) -> Signature:
        k = self.deterministic_k(z)
        r = (k * S256_G).x.num
        k_inv = pow(k, S256_N - 2, S256_N)
        s = (z + r * self.secret) * k_inv % S256_N

        if s > S256_N / 2:
            s = S256_N - s

        return Signature(r, s)

    def deterministic_k(self, z: int) -> int:
        k = b'\x00' * 32
        v = b'\x01' * 32

        if z > S256_N:
            z -= S256_N

        z_bytes = z.to_bytes(32, 'big')
        secret_bytes = self.secret.to_bytes(32, 'big')

        s256 = hashlib.sha256

        k = hmac.new(k, v + b'\x00' + secret_bytes + z_bytes, s256).digest()
        v = hmac.new(k, v, s256).digest()
        k = hmac.new(k, v + b'\x01' + secret_bytes + z_bytes, s256).digest()
        v = hmac.new(k, v, s256).digest()

        while True:
            v = hmac.new(k, v, s256).digest()
            candidate = int.from_bytes(v, 'big')

            if candidate >= 1 and candidate < S256_N:
                return candidate

            k = hmac.new(k, v + b'\x00', s256).digest()
            v = hmac.new(k, v, s256).digest()
