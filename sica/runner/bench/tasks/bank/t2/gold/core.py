class Account:
    def __init__(self, balance=0):
        self.balance = balance

def transfer(src, dst, amount):
    if amount > src.balance:
        raise ValueError('insufficient funds')
    src.balance -= amount
    dst.balance += amount
    return amount
