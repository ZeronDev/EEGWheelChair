import customtkinter as ctk
import config
from config import path
from PIL import Image
from hardware import Hardware

class HamsterControl(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master, border_color="#1360A2")
        self.direction = ctk.CTkFrame(master=self, fg_color="transparent")
        self.direction.place(relx=0.5, rely=0.5, anchor="center")
        self.color = "#d9d9d9"
        self.hamster = Hardware()

        self.defaultLeft = ctk.CTkImage(light_image=Image.open(path("images", "light", "left.png")), dark_image=Image.open(path("images", "dark", "left.png")), size=(120,120))
        self.enabledLeft = ctk.CTkImage(light_image=Image.open(path("images", "left.png")), size=(120,120))
        self.defaultRight = ctk.CTkImage(light_image=Image.open(path("images", "light", "right.png")), dark_image=Image.open(path("images", "dark", "right.png")), size=(120,120))
        self.enabledRight = ctk.CTkImage(light_image=Image.open(path("images", "right.png")), size=(120,120))
        self.left = ctk.CTkLabel(master=self.direction, image=self.defaultLeft, fg_color=self.color, text="", corner_radius=5)
        self.right = ctk.CTkLabel(master=self.direction, image=self.defaultRight, fg_color=self.color, text="", corner_radius=5)

        self.left.grid(row=0, column=0, padx=20, pady=20)
        self.right.grid(row=0, column=1, padx=20, pady=20)
        self.moving = False

    def changeColor(self):
        if config.isDarkMode:
            self.color = "#292929"
        else:
            self.color = "#d9d9d9"
        self.left.configure(fg_color=self.color)
        self.right.configure(fg_color=self.color)

    def activate(self, number):
        match number:
            case 0:
                self.left.configure(image=self.enabledLeft)
            case 1:
                self.right.configure(image=self.enabledRight)
    def deactivate(self):
        self.left.configure(image=self.defaultLeft)
        self.right.configure(image=self.defaultRight)
    def blink(self):
        self.moving = not self.moving

        if self.moving:
            self.configure(border_width=10)
        else:
            self.configure(border_width=0)
    def forward(self):
        if self.moving:
            self.hamster.forward()
    