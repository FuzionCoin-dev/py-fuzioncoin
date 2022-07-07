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

def address_generator(pubkey: ecc.S256Point) -> str:
    data = pubkey.x.num.to_bytes(32, "big") + pubkey.y.num.to_bytes(32, "big")
    mainpart = hashlib.blake2b(hashlib.sha256(data).digest(), digest_size=20).digest()
    checksum = hashlib.sha256(mainpart).digest()[:4]
    return "0x" + (checksum + mainpart).hex()

################################################################
# SIMPLE TO USE Signature, PrivateKey AND PublicKey OBJECTS
################################################################

class Signature:
    def __init__(self, r, s):
        self.content = ecc.Signature(r, s)

    def serialize(self) -> str:
        return json.dumps({
            "type": "signature",
            "r": self.content.r,
            "s": self.content.s
        })

    def __repr__(self) -> str:
        return self.content.__repr__()

    def __eq__(self, other) -> bool:
        return self.content.r == other.content.r and self.content.s == other.content.s

    def __ne__(self, other) -> bool:
        return not self == other

    @classmethod
    def parse(cls, serialization):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        if not "type" in data:
            raise ValueError("Invalid JSON serialization")

        if str(data["type"]).lower() != "signature":
            raise ValueError("This is not Signature JSON serialization")

        try:
            return cls(
                r = data["r"],
                s = data["s"]
            )
        except KeyError:
            raise ValueError("Invalid JSON serialization")


class PrivateKey:
    def __init__(self, secret: int = None):
        if secret is None:
            secret = generate_secret_key()

        self.content = ecc.PrivateKey(secret)

    def sign(self, message: bytes) -> Signature:
        z = int.from_bytes(hash256(message), "big")

        s1 = self.content.sign(z)

        return Signature(s1.r, s1.s)

    def serialize(self) -> bytes:
        return json.dumps({
            "type": "privatekey",
            "secret": self.content.secret
        })

    def __eq__(self, other) -> bool:
        return self.content.secret == other.content.secret

    def __ne__(self, other) -> bool:
        return not self == other

    def __repr__(self) -> str:
        return f"PrivateKey({self.content.secret})"

    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        if not "type" in data:
            raise ValueError("Invalid JSON serialization")

        if str(data["type"]).lower() != "privatekey":
            raise ValueError("This is not PrivateKey JSON serialization")

        try:
            return cls(
                secret = data["secret"]
            )
        except KeyError:
            raise ValueError("Invalid JSON serialization")

class PublicKey:
    def __init__(self, privkey: PrivateKey, content = None):
        if content is None:
            self.content = privkey.content.point
        else:
            self.content = content

        self.address = address_generator(self.content)

    def verify(self, message: bytes, signature: Signature) -> bool:
        z = int.from_bytes(hash256(message), "big")

        return self.content.verify(z, signature.content)

    def serialize(self) -> str:
        return json.dumps({
            "type": "publickey",
            "x": self.content.x.num,
            "y": self.content.y.num,
        })

    def __eq__(self, other) -> bool:
        return self.content == other.content

    def __ne__(self, other) -> bool:
        return not self == other

    def __repr__(self) -> str:
        return f"PublicKey(x={self.content.x.num}, y={self.content.y.num})"

    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        if not "type" in data:
            raise ValueError("Invalid JSON serialization")

        if str(data["type"]).lower() != "publickey":
            raise ValueError("This is not PublicKey JSON serialization")

        try:
            return cls(
                privkey = None,
                content = ecc.S256Point(
                    x = data["x"],
                    y = data["y"]
                )
            )
        except KeyError:
            raise ValueError("Invalid JSON serialization")

################################################################
# ACTUAL BLOCKCHAIN
################################################################

class Transaction:
    def __init__(self, sender: PublicKey, recipient: str, amount: int, signature: ecc.Signature = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount       # 1 means 1/10000000000 of FUZC

        self.datatext = self.sender.serialize() + self.recipient.encode("ascii") + self.amount.to_bytes((self.amount.bit_length() + 7) // 8, "big")

        if signature is not None:
            if not self.verify():
                raise ValueError("Invalid signature")

        self.signature = signature

    def sign(self, privkey: PrivateKey):
        if self.signature is not None:
            raise ValueError("This transaction is already signed")

        if PublicKey(privkey) != self.sender:
            raise ValueError("This private key does not belong to sender")

        self.signature = privkey.sign(self.datatext)

    def verify(self) -> bool:
        return

    def serialize(self) -> bytes:
        return self.signature.serialize() + self.datatext

    def __repr__(self) -> str:
        return f"tx:\n sender: {self.sender}\n recipient: {self.recipient}\n amount: {self.amount}"

    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        version = data["ver"]
        inputs = data["in"]
        outputs = data["out"]
        locktime = data["lt"]

        return cls(version, inputs, outputs, locktime)


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
