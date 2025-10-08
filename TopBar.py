import customtkinter as ctk
from PIL import Image
from config import path, FONT

class TopBar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master)
         
        self.logo = ctk.CTkLabel(master=self,image=ctk.CTkImage(Image.open(path("images", "LOGO.png")), size=(60,60)), text="   뇌파 휠체어 조종 어플리케이션", font=FONT, compound="left")
        self.maker = ctk.CTkLabel(master=self, width=80, height=30, text="by SICC", font=FONT)

        self.logo.grid(row=0, column=0, sticky="nsw", padx=(10,20), pady=10)
        self.maker.grid(row=0, column=1, sticky="w", padx=10)