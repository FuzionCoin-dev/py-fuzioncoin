import hashlib
import secrets
import json

import ecc

################################################################
# USEFUL FUNCTIONS
################################################################

def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def generate_secret_key() -> int:
    x = secrets.token_bytes(4096)
    h = hash256(x)

    return int.from_bytes(h, "big")

def address_generator(pubkey: ecc.Point) -> str:
    data = pubkey.sec(True)
    mainpart = hashlib.blake2b(hashlib.sha256(data).digest(), digest_size=20).digest()
    checksum = hashlib.sha256(mainpart).digest()[:4]
    return "0x" + (checksum + mainpart).hex()

################################################################
# SIMPLER PrivateKey AND PublicKey OBJECTS
################################################################

class PrivateKey:
    def __init__(self, secret: int = None):
        if secret is None:
            secret = generate_secret_key()

        self.content = ecc.PrivateKey(secret)

    def sign(self, message: bytes) -> ecc.Signature:
        z = int.from_bytes(hash256(message), "big")

        return self.content.sign(z)

    def wif(self, compression=True) -> str:
        return self.content.wif(compression)

    def serialize(self, compression=True) -> bytes: # Does the same thing as wif(), but returns bytes instead of str; for unification
        return self.wif(compression).encode("ascii")

    def __eq__(self, other) -> bool:
        return self.content.secret == other.content.secret

    def __repr__(self) -> str:
        return f"PrivateKey({self.content.secret})"

    @classmethod
    def parse(cls, wif_str: str):
        if isinstance(wif_str, bytes):
            wif_str = wif_str.decode("ascii")

        return cls(ecc.PrivateKey.parse(wif_str).secret)

class PublicKey:
    def __init__(self, privkey: PrivateKey, content = None):
        if content is None:
            self.content = privkey.content.point
        else:
            self.content = content

        self.address = address_generator(self.content)

    def verify(self, message: bytes, signature: ecc.Signature) -> bool:
        z = int.from_bytes(hash256(message), "big")

        return self.content.verify(z, signature)

    def sec(self, compression=True) -> bytes:
        return self.content.sec(compression)

    def serialize(self, compression=True) -> bytes:  # Does the same thing as sec(); for unification
        return self.sec(compression)

    def __eq__(self, other) -> bool:
        return self.content== other.content

    def __repr__(self) -> str:
        return f"PublicKey(x={self.content.x.num}, y={self.content.y.num})"

    @classmethod
    def parse(cls, sec_bin):
        return cls(None, ecc.S256Point.parse(sec_bin))

################################################################
# ACTUAL BLOCKCHAIN
################################################################

class Transaction:
    def __init__(self, version, inputs, outputs, locktime):
        self.version = version
        self.inputs = inputs
        self.outputs = outputs
        self.locktime = locktime

    def __repr__(self) -> str:
        inputs = ""

        for input in self.inputs:
            inputs += f"{input.__repr__()}\n"

        outputs = ""

        for output in self.outputs:
            outputs += f"{output.__repr__()}\n"

        return f"tx: {self.id()}\nver: {self.version}\nin:\n{inputs}\nout:\n{outputs}\nlocktime: {self.locktime}"

    def hash(self) -> bytes:
        return hash256(self.serialize())

    def id(self) -> str:
        return self.hash().hex()

    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except:
            raise ValueError("Cannot parse JSON serialization")

        version = data["version"]
        inputs = data["inputs"]
        outputs = data["outputs"]

        # TODO


class Block:
    def __init__(self, height: int, transactions: list, perv_hash: str = "0"*64, nonce: int = 0):
        self.height = height
        self.transactions = transactions
        self.perv_hash = perv_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        hashing_text = f"{self.height}#{self.perv_hash}#{t for t in self.transactions}#{self.nonce}"

        h = sha256(hashing_text.encode("utf-8")).hexdigest()
        h2 = sha256(h.encode("utf-8")).hexdigest()

        return h2

class Blockchain:
    def __init__(self):
        self.block_list = []
        self.difficulty = 6

    def add_block(self, block: Block):
        self.block_list.append(block)

    def get_block(self, pos: int) -> Block:
        return self.block_list[pos]

    def mine(self, block: Block):
        while True:
            hash = block.calculate_hash()
            if hash[:self.difficulty] == "0"*self.difficulty:
                block.hash = hash
                break

            block.nonce += 1

        self.add_block(block)
