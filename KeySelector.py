import customtkinter as ctk
import os
from PIL import Image
from config import path, toggleAbility
import config
from InputDialog import CustomInputDialog, DeleteInputDialog
from functools import partial
from Keybind import KeybindSelector
import DataManager

addImage = ctk.CTkImage(dark_image=Image.open(path("images", "add.png")), size=(22, 22))
deleteImage = ctk.CTkImage(dark_image=Image.open(path("images", "delete.png")), size=(22, 22))
folderImage = ctk.CTkImage(dark_image=Image.open(path("images", "folder.png")), size=(22, 22))
refreshImage = ctk.CTkImage(dark_image=Image.open(path("images", "refresh.png")), size=(22, 22))

class KeySelector(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master, corner_radius=7)
        topBar = ctk.CTkFrame(master=self, height=20, corner_radius=0)
        topBar.pack(fill="x", anchor="n")
        dirLoc = ctk.CTkLabel(master=topBar,text=os.getcwd(), fg_color="transparent", font=("맑은 고딕", 15))
        dirLoc.pack(side="left", padx=6, pady=3)

        delete = ctk.CTkLabel(master=topBar, image=deleteImage, text="")
        delete.pack(side="right", padx=3, pady=3)
        delete.bind(sequence="<Button-1>", command=self.deleteButton)

        add = ctk.CTkLabel(master=topBar, image=addImage, text="")
        add.pack(side="right", padx=3, pady=3)
        add.bind(sequence="<Button-1>", command=self.addButton)

        folder = ctk.CTkLabel(master=topBar, image=folderImage, text="")
        folder.pack(side="right", padx=3, pady=3)
        folder.bind(sequence="<Button-1>", command=self.dirButton) #TODO PARTIAL 삭제함
        
        refresh = ctk.CTkLabel(master=topBar, image=refreshImage, text="")
        refresh.pack(side="right", padx=3, pady=3)
        refresh.bind(sequence="<Button-1>", command=self.refreshButton)

        DataManager.keybindWidget = KeybindSelector(self)
        DataManager.keybindWidget.pack(fill="both", expand=True)

    def refreshButton(self, *_):
        if config.disabled: return
        DataManager.keybindWidget.refresh()

    def dirButton(self, *_):
        if config.disabled: return
        os.startfile(path("data"))
    def addButton(self, *_):
        if not config.disabled and config.other_screen == None:
            toggleAbility()
            config.other_screen = CustomInputDialog("데이터 파일 생성")
            config.other_screen.focus()
            config.other_screen.grab_set()
            config.other_screen.wait_window()

            name = config.other_screen.getData()
            config.other_screen = None
            toggleAbility()
            if name and name not in os.listdir(path=path("data")):
                try:
                    open(path("data", name+".csv"), "w").close()
                except OSError: #잘못된 파일 이름
                    pass
            self.refreshButton()
    def deleteButton(self, *_):
            
        if not config.disabled and config.other_screen == None:
            toggleAbility()
            config.other_screen = DeleteInputDialog("데이터 파일 삭제")
            config.other_screen.focus()
            config.other_screen.grab_set()
            config.other_screen.wait_window()

            names = config.other_screen.getData()
            config.other_screen = None
            toggleAbility()
            if names:
                for name in names:
                    if name+".csv" in os.listdir(path=path("data")):
                        try:
                            os.remove(path("data", name+".csv"))
                            if DataManager.keybindMap.get(name, None):
                                del DataManager.keybindMap[name]
                        except OSError:
                            pass
            self.refreshButton()