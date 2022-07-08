import hashlib
import secrets
import json

import ecc
import logger

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

def get_difficulty(height: int) -> int:
    start_difficulty = 5

    return start_difficulty + (height // 100000) # difficulty of mining increases every 100000 blocks

################################################################
# SIMPLE TO USE Signature, PrivateKey AND PublicKey OBJECTS
################################################################

class Signature:
    def __init__(self, r, s):
        self.content = ecc.Signature(r, s)

    def serialize(self) -> str:
        return json.dumps({
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

        try:
            return cls(
                r = data["r"],
                s = data["s"]
            )
        except KeyError:
            raise ValueError("This is not valid Signature JSON serialization")


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

        try:
            return cls(
                secret = data["secret"]
            )
        except KeyError:
            raise ValueError("This is not valid PrivateKey JSON serialization")

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

        try:
            return cls(
                privkey = None,
                content = ecc.S256Point(
                    x = data["x"],
                    y = data["y"]
                )
            )
        except KeyError:
            raise ValueError("This is not valid PublicKey JSON serialization")

################################################################
# ACTUAL BLOCKCHAIN
################################################################

class Transaction:
    def __init__(self, sender: PublicKey, recipient: str, amount: int, signature: Signature = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount       # 1 means 1/10000000000 of FUZC

        if signature is not None:
            if not self.verify():
                raise ValueError("Invalid signature")

        self.signature = signature

    def sign(self, privkey: PrivateKey):
        if self.signature is not None:
            raise ValueError("This transaction is already signed")

        if PublicKey(privkey) != self.sender:
            raise ValueError("This private key does not belong to sender")

        m_sender = self.sender.content.x.num.to_bytes(32, "big") + self.sender.content.y.num.to_bytes(32, "big") # 64 bytes
        m_recipient = self.recipient.encode("ascii") # 50 bytes
        m_amount = self.amount.to_bytes((self.amount.bit_length() + 7) // 8, "big") # variable size

        m = m_sender + m_recipient + m_amount

        self.signature = privkey.sign(m)

    def verify(self) -> bool:
        m_sender = self.sender.content.x.num.to_bytes(32, "big") + self.sender.content.y.num.to_bytes(32, "big") # 64 bytes
        m_recipient = self.recipient.encode("ascii") # 50 bytes
        m_amount = self.amount.to_bytes((self.amount.bit_length() + 7) // 8, "big") # variable size

        m = m_sender + m_recipient + m_amount

        return self.sender.verify(m, self.signature)

    def hash(self) -> bytes:
        m_sender = self.sender.content.x.num.to_bytes(32, "big") + self.sender.content.y.num.to_bytes(32, "big") # 64 bytes
        m_recipient = self.recipient.encode("ascii") # 50 bytes
        m_amount = self.amount.to_bytes((self.amount.bit_length() + 7) // 8, "big") # variable size

        m = m_sender + m_recipient + m_amount

        return hash256(m)

    def serialize(self) -> str:
        return json.dumps({
            "sender": self.sender.serialize(),
            "recipient": self.recipient,
            "amount": self.amount,
            "signature": self.signature.serialize(),
            "hash": self.hash().hex()
        })

    def __repr__(self) -> str:
        return f"tx:\n sender: {self.sender.address}\n recipient: {self.recipient}\n amount: {self.amount}\n signed: {self.signature is not None}"

    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        try:
            return cls(
                sender = PublicKey.parse(data["sender"]),
                recipient = data["recipient"],
                amount = data["amount"],
                signature = Signature.parse(data["signature"])
            )
        except KeyError:
            raise ValueError("This is not valid Transaction serialization")

class Block:
    def __init__(self, height: int, transactions: List[Transaction], prev_hash: str = None, nonce: int = None):
        self.height = height
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.nonce = nonce

        if self.prev_hash is None:
            self.prev_hash = bytes(32)

        if self.nonce is None:
            self.nonce = 0

    def hash(self) -> bytes:
        m =  len(self.transactions).to_bytes(4, "big") # max 2^32 transactions per block
        m += b"".join([tx.hash() for tx in self.transactions])
        m += self.prev_hash
        m += self.nonce.to_bytes(8, "big")

        return hash256(m)

    def serialize(self) -> str:
        return json.dumps({
            "height": self.height,
            "transactions": [tx.serialize() for tx in self.transactions],
            "prev_hash": self.prev_hash.hex(),
            "nonce": self.nonce,
            "hash": self.hash().hex()
        })

    def mine(self):
        difficulty = get_difficulty(self.height)

        while self.hash()[0:difficulty] != bytes(difficulty):
            self.nonce += 1
        
        logger.Logger("MINER").info(f"Block mined:\n    height: {self.height}\n    hash: {self.hash().hex()}\n    nonce: {self.nonce}")

    def validate(self) -> bool:
        difficulty = get_difficulty(self.height)

        if self.hash()[0:difficulty] != bytes(difficulty):
            return False

        for tx in self.transactions:
            if not tx.verify():
                return False

        return True

    def __repr__(self) -> str:
        return f"Block:\n height: {self.height}\n hash: {self.hash().hex()}\n nonce: {self.nonce}\n transactions: {len(self.transactions)}"
    
    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        try:
            return cls(
                transactions = [Transaction.parse(tx) for tx in data["transactions"]],
                prev_hash = bytes.fromhex(data["prev_hash"]),
                nonce = data["nonce"]
            )
        except KeyError:
            raise ValueError("This is not valid Block serialization")

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
