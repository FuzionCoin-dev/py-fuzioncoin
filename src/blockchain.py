from hashlib import sha256
import ecdsa

class PrivateKey:
    def __init__(self):
        self.content = ecdsa.SigningKey.generate()
        self.pem = self.content.to_pem()

    def sign(self, message):
        signature = self.content.sign(message)
        return signature

    def __str__(self) -> str:
        return self.content.to_string()

class PublicKey:
    def __init__(self, privkey: PrivateKey):
        self.content = privkey.content.verifying_key
        self.pem = self.content.to_pem()

    def verify(self, message, signature) -> bool:
        try:
            self.content.verify(signature, message)
            return True
        except ecdsa.BadSignatureError:
            return False

    def __str__(self) -> str:
        return self.content.to_string()

class Transaction:
    def __init__(self, sender: PublicKey, recipient: PublicKey, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = None

    def str_nosig(self) -> list:
        return f"{self.sender}:{self.recipient}:{self.amount}"

    def __str__(self) -> str:
        if self.signature is None:
            return self.str_nosig()

        return f"{self.sender}:{self.recipient}:{self.amount}:{self.signature}"

    def sign(self, privkey):
        self.signature = privkey.sign(self.str_nosig().encode("utf-8"))

    def verify_signature(self, pubkey):
        return pubkey.verify(self.signature, self.str_nosig().encode("utf-8"))

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
