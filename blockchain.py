class Transaction:
    def __init__(self, sender: Address, recipient: Address, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = None

    def sign(self, privkey):
        # TODO: this
        pass

    def verify(self, pubkey):
        # TODO: this
        pass

    def __str__(self):
        return f"{self.sender}:{self.recipient}:{self.amount}:{self.signature}"

class Block:
    def __init__(self, height: int, perv_hash: str, transactions: list[Transaction], nonce: int = 0):
        self.height = height
        self.perv_hash = perv_hash
        self.transactions = transactions
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        hashing_text = f"{self.height}#{self.perv_hash}#{t for t in self.transactions}#{self.nonce}"

        # TODO: calculate twice sha256 of hashing_text

        return "x"
