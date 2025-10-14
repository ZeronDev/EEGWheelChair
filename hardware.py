from roboid import HamsterS, wait

class Hardware:
    def __init__(self):
        self.hamster = HamsterS()
        self.isMoving = False
        self.isForward = False
    def forward(self):
        if self.isMoving:
            return
        self.isMoving = True
        self.lightOn()
        self.hamster.wheels(30)
    def stop(self):
        self.isMoving = False
        self.hamster.stop()
        self.lightOff()
    def leftward(self):
        if self.isMoving:
            return
        self.isMoving = True
        self.hamster.wheels(-30, 30)
        self.lightOn()
        wait(1000)
        self.stop()
    def rightward(self):
        if self.isMoving:
            return
        self.isMoving = True
        self.hamster.wheels(30, -30)
        self.lightOn()
        wait(1000)
        self.stop()
    def lightOn(self):
        self.hamster.leds(1)
    def lightOff(self):
        self.hamster.leds(0)

