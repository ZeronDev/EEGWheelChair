from roboid import HamsterS

class Hardware:
    def __init__(self):
        self.hamster = HamsterS()
    def forward(self):
        self.hamster.wheels(30)
    def backward(self):
        self.hamster.wheels(-30)
    def leftward(self):
        self.hamster.wheels(-30, 30)
    def rightward(self):
        self.hamster.wheels(30, -30)
