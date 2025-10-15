import customtkinter as ctk
import config
from config import path
from PIL import Image
from roboid import HamsterS, wait
import asyncio

class HamsterControl(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master, border_color="#1360A2")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.direction = ctk.CTkFrame(master=self, fg_color="transparent")
        self.direction.grid(row=0, column=0, padx=20, pady=20)
        self.color = "#d9d9d9"
        self.hamster = HamsterS()
        self.isMoving = False

        self.defaultLeft = ctk.CTkImage(light_image=Image.open(path("images", "light", "left.png")), dark_image=Image.open(path("images", "dark", "left.png")), size=(120,120))
        self.enabledLeft = ctk.CTkImage(light_image=Image.open(path("images", "left.png")), size=(120,120))
        self.defaultRight = ctk.CTkImage(light_image=Image.open(path("images", "light", "right.png")), dark_image=Image.open(path("images", "dark", "right.png")), size=(120,120))
        self.enabledRight = ctk.CTkImage(light_image=Image.open(path("images", "right.png")), size=(120,120))
        self.left = ctk.CTkLabel(master=self.direction, image=self.defaultLeft, fg_color=self.color, text="", corner_radius=5)
        self.right = ctk.CTkLabel(master=self.direction, image=self.defaultRight, fg_color=self.color, text="", corner_radius=5)

        self.left.grid(row=0, column=0, padx=20, pady=20)
        self.right.grid(row=0, column=1, padx=20, pady=20)

    def changeColor(self):
        if config.isDarkMode:
            self.color = "#292929"
        else:
            self.color = "#d9d9d9"
        self.left.configure(fg_color=self.color)
        self.right.configure(fg_color=self.color)

    def activate(self, number):
        if self.isMoving:
            return
        match number:
            case 0:
                self.left.configure(image=self.enabledLeft)
                asyncio.run(self.leftward())
            case 1:
                self.right.configure(image=self.enabledRight)
                asyncio.run(self.rightward())

    def deactivate(self):
        self.left.configure(image=self.defaultLeft)
        self.right.configure(image=self.defaultRight)
        
    def blink(self):
        if not self.isMoving:
            asyncio.run(self.forward())
            
    async def forward(self):
        if self.isMoving:
            return
        self.isMoving = True
        self.lightOn()
        self.hamster.wheels(50)
        await asyncio.sleep(1)
        self.stop()

    def stop(self):
        self.isMoving = False
        self.hamster.stop()
        self.lightOff()
        self.deactivate()
        
    async def leftward(self):
        if self.isMoving:
            return
        self.isMoving = True
        self.hamster.wheels(35, -35)
        self.lightOn()
        await asyncio.sleep(0.7)
        self.stop()

    async def rightward(self):
        if self.isMoving:
            return
        self.isMoving = True
        self.hamster.wheels(-35, 35)
        self.lightOn()
        await asyncio.sleep(0.7)
        self.stop()

    def lightOn(self):
        self.hamster.leds(1)
    def lightOff(self):
        self.hamster.leds(0)

