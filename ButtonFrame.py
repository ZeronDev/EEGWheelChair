import customtkinter as ctk
from config import buttonGenerate
from functools import partial
import Muse

class ButtonFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master, fg_color="transparent")

        self.grid_columnconfigure((0,1,2), weight=1)

        self.recordButton = buttonGenerate(master=self, text="기록", row=0, column=0)
        self.recordButton.configure(command=partial(Muse.record, self))
        self.learnButton = buttonGenerate(master=self, text="학습", row=0, column=1)
        self.learnButton.configure(command=Muse.learn)
        self.runButton = buttonGenerate(master=self, text="실행", row=0, column=2)
        self.runButton.configure(command=partial(Muse.run, self))