class Account:
    def __init__(self, balance=0):
        self.balance = balance

def transfer(src, dst, amount):
    dst.balance += amount
    return amount
