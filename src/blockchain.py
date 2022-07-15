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

def get_difficulty(height: int) -> int:
    start_difficulty = 6

    return start_difficulty + (height // 100000) # difficulty of mining increases every 100000 blocks

def get_block_reward(height: int) -> int:
    start_reward = 50 * 10**9

    if height < 100000:
        return start_reward

    return int(start_reward / (2 * (height // 100000))) # reward of mining decrases every 100000 blocks

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
    def __init__(self, sender: PublicKey, recipient: str, amount: int, prev_hash: bytes, signature: Signature = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount       # 1 means 1/000000000 of FUZC
        self.prev_hash = prev_hash

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

        m = self.prev_hash + m_sender + m_recipient + m_amount

        self.signature = privkey.sign(m)

    def verify(self) -> bool:
        m_sender = self.sender.content.x.num.to_bytes(32, "big") + self.sender.content.y.num.to_bytes(32, "big") # 64 bytes
        m_recipient = self.recipient.encode("ascii") # 50 bytes
        m_amount = self.amount.to_bytes((self.amount.bit_length() + 7) // 8, "big") # variable size

        m = self.prev_hash + m_sender + m_recipient + m_amount

        return self.sender.verify(m, self.signature)

    def hash(self) -> bytes:
        m_sender = self.sender.content.x.num.to_bytes(32, "big") + self.sender.content.y.num.to_bytes(32, "big") # 64 bytes
        m_recipient = self.recipient.encode("ascii") # 50 bytes
        m_amount = self.amount.to_bytes((self.amount.bit_length() + 7) // 8, "big") # variable size

        m = self.prev_hash + m_sender + m_recipient + m_amount

        return hash256(m)

    def serialize(self) -> str:
        return json.dumps({
            "sender": self.sender.serialize(),
            "recipient": self.recipient,
            "amount": self.amount / 1000000000,
            "signature": self.signature.serialize(),
            "prev_hash": self.prev_hash.hex(),
            "hash": self.hash().hex()
        })

    def __repr__(self) -> str:
        return f"tx:\n sender: {self.sender.address}\n recipient: {self.recipient}\n amount: {self.amount}\n signed: {self.signature is not None}"

    def __eq__(self, other):
        return self.hash() == other.hash()

    def __ne__(self, other):
        return not self == other

    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        try:
            out =  cls(
                sender = PublicKey.parse(data["sender"]),
                recipient = data["recipient"],
                amount = int(data["amount"] * 1000000000),
                prev_hash = bytes.fromhex(data["prev_hash"]),
                signature = Signature.parse(data["signature"])
            )

            if out.hash().hex() != data["hash"]:
                raise ValueError("Invalid hash in JSON serialization")
            
        except KeyError:
            raise ValueError("This is not valid Transaction JSON serialization")

class CoinbaseTransaction(Transaction):
    def __init__(self, height: int, recipient: str, prev_hash: bytes):
        super().__init__(
            sender = None,
            recipient = recipient,
            amount = get_block_reward(height),
            prev_hash = prev_hash
        )

        self.height = height

    def sign(self, privkey: PrivateKey):
        raise NotImplementedError("Coinbase transactions cannot be signed")

    def verify(self) -> bool:
        return self.amount == get_block_reward(self.height)

    def hash(self) -> bytes:
        return hash256(self.prev_hash + self.recipient.encode("ascii") + self.amount.to_bytes((self.amount.bit_length() + 7) // 8, "big"))

    def serialize(self) -> str:
        return json.dumps({
            "height": self.height,
            "recipient": self.recipient,
            "amount": self.amount / 1000000000,
            "prev_hash": self.prev_hash.hex(),
            "hash": self.hash().hex()
        })

    def __repr__(self) -> str:
        return f"coinbase:\n recipient: {self.recipient}\n amount: {self.amount}\n height: {self.height}"

    @classmethod
    def parse(cls, serialization: str):
        try:
            data = json.loads(serialization)
        except json.JSONDecodeError:
            raise ValueError("Cannot parse JSON serialization")

        try:
            out =  cls(
                height = int(data["height"]),
                recipient = data["recipient"],
                prev_hash = bytes.fromhex(data["prev_hash"])
            )

            if out.hash().hex() != data["hash"]:
                raise ValueError("Invalid hash in JSON serialization")
            
        except KeyError:
            raise ValueError("This is not valid CoinbaseTransaction JSON serialization")

class Block:
    def __init__(self, height: int, transactions: list[Transaction], prev_hash: str = None, nonce: int = None):
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
        m += self.nonce.to_bytes(16, "big")

        return hash256(m)

    def serialize(self) -> str:
        return json.dumps({
            "height": self.height,
            "transactions": [tx.serialize() for tx in self.transactions],
            "prev_hash": self.prev_hash.hex(),
            "nonce": self.nonce,
            "hash": self.hash().hex()
        })

    def mine(self, reward_address: str, prev_tx_hash: bytes):
        if len(self.transactions) > 0:
            prev_tx_hash = self.transactions[-1].hash()

        self.transactions.append(
            CoinbaseTransaction(
                height = self.height,
                recipient = reward_address,
                prev_hash = prev_tx_hash
            )
        )

        difficulty = get_difficulty(self.height)
        self.nonce = 0

        while self.hash().hex()[0:difficulty] != "0" * difficulty:
            self.nonce += 1

    def validate(self) -> bool:
        difficulty = get_difficulty(self.height)

        if self.hash().hex()[0:difficulty] != "0" * difficulty:
            return False

        for tx in self.transactions:
            if not tx.verify():
                return False

        return True

    def __repr__(self) -> str:
        return f"block:\n height: {self.height}\n hash: {self.hash().hex()}\n nonce: {self.nonce}\n transactions: {len(self.transactions)}"
    
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
        self.chain = []
        self.pending_transactions = []

    def add_block(self, block: Block):
        if not block.validate():
            raise ValueError("Invalid block")

        if len(self.chain) > 0:
            if block.prev_hash != self.chain[-1].hash():
                raise ValueError("Invalid or late block")
        else:
            if block.prev_hash != bytes(32):
                raise ValueError("Previous hash of genesis block is not zero")

        self.chain.append(block)

    def add_transaction(self, tx: Transaction):
        if not tx.verify():
            raise ValueError("Invalid transaction")
        
        self.pending_transactions.append(tx)

    def create_transaction(self, tx: Transaction):
        self.add_transaction(tx)

        # TODO: broadcast new transaction to all nodes

    def mine(self, reward_address: str):
        if len(self.chain) > 0:
            last_block_hash = self.chain[-1].hash()
            lest_tx_hash = self.chain[-1].transactions[-1].hash()
        else:
            last_block_hash = bytes(32)
            lest_tx_hash = bytes(32)

        new_block = Block(
            height = len(self.chain),
            transactions = self.pending_transactions,
            prev_hash = last_block_hash
        )

        new_block.mine(
            reward_address = reward_address,
            prev_tx_hash = lest_tx_hash
        )

        for tx in self.pending_transactions.copy():
            if tx in new_block.transactions:
                try:
                    self.pending_transactions.remove(tx)
                except ValueError:
                    pass

        self.add_block(new_block)

        # TODO: broadcast new block to all nodes
