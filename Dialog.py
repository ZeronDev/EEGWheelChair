import customtkinter as ctk
from functools import partial
from config import FONT

class RecordSelectDialog(ctk.CTkToplevel):
    def __init__(self, title="데이터의 종류를 선택해주세요"):
        super().__init__()

        self.title(title)
        self.geometry("380x160")
        self.resizable(False, False)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1), weight=1)
        self.input = ""
        self.var = ctk.StringVar(value="")

        self.frame = ctk.CTkFrame(master=self)
        self.frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=(10, 15))

        confirm = ctk.CTkButton(master=self, text="확인", command=partial(self.confirmButton, self), font=FONT)
        confirm.grid(row=1, column=0, padx=(20, 10), pady=(0, 5), sticky="new")
        close = ctk.CTkButton(master=self, text="취소", command=partial(self.closeButton, self), font=FONT)
        close.grid(row=1, column=1, padx=(10, 20), pady=(0, 5), sticky="new")

        for (element, fileName) in zip(["기본 상태", "왼쪽", "오른쪽"], ["base", "left", "right"]):
            radio = ctk.CTkRadioButton(master=self.frame, text=element, variable=self.var, value=fileName, font=FONT)
            radio.pack(side="top", anchor="w", padx=7, pady=5)
        
    
    def confirmButton(self, _):
        self.input = self.var.get()
        self.destroy()
    def closeButton(self, _):
        self.destroy()    
    def getData(self):
        result = self.input.strip()
        
        if result:
            return result
        else:
            return None
