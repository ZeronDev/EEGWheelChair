import customtkinter as ctk
from functools import partial
import DataManager
from config import path

class CustomInputDialog(ctk.CTkToplevel):
    def __init__(self, title, custom=False):
        super().__init__()

        self.title(title)
        self.geometry("380x160")
        self.resizable(False, False)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1), weight=1)
        if not custom: 
            self.entry()
            self.buttons() 
        self.input = ""
    def buttons(self):
        confirm = ctk.CTkButton(master=self, text="확인", command=partial(self.confirmButton, self), font=("맑은 고딕", 20))
        confirm.grid(row=1, column=0, padx=(20, 10), pady=(0, 5), sticky="new")
        close = ctk.CTkButton(master=self, text="취소", command=partial(self.closeButton, self), font=("맑은 고딕", 20))
        close.grid(row=1, column=1, padx=(10, 20), pady=(0, 5), sticky="new")
    def entry(self):
        self.entry = ctk.CTkEntry(master=self, placeholder_text="파일 이름", height=50, font=("맑은 고딕", 20))
        self.entry.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=15)
        self.entry.focus()
    def confirmButton(self, _):
        self.input = self.entry.get()
        self.destroy()
    def closeButton(self, _):
        self.destroy()    
    def getData(self):
        result = self.input.strip()
        
        if result:
            return result
        else:
            return None

class DeleteInputDialog(CustomInputDialog):
    def __init__(self, title):
        super().__init__(title, True)
        self.geometry("380x300")
        self.entry = ctk.CTkScrollableFrame(master=self, corner_radius=7)
        self.entry.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=(10, 15))
        self.varList = []
        for element in DataManager.eegData:
            var = ctk.StringVar(value="")
            self.varList.append(var)
            checkbox = ctk.CTkCheckBox(master=self.entry, text=element, variable=var, onvalue=element, offvalue="")
            checkbox.pack(side="top", anchor="w", padx=7, pady=5)
        super().buttons()
        
    def confirmButton(self, _):
        self.input = [x.get() for x in self.varList if x.get()]
        self.destroy()
    def getData(self):
        result = self.input
        if result:
            return result
        else:
            return None
class SelectInputDialog(CustomInputDialog):
    def __init__(self, title):
        super().__init__(title, True)
        self.geometry("380x300")
        self.entry = ctk.CTkScrollableFrame(master=self, corner_radius=7)
        self.entry.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=(10, 15))
        self.var = ctk.StringVar(value="")
        for element in DataManager.eegData:
            radio = ctk.CTkRadioButton(master=self.entry, text=element, variable=self.var, value=element)
            radio.pack(side="top", anchor="w", padx=7, pady=5)
        super().buttons()
    def confirmButton(self, _):
        self.input = self.var
        self.destroy()
    def getData(self):
        result = self.input
        if result:
            return result
        else:
            return None