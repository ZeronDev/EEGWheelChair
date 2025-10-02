import customtkinter as ctk
import os
import config
import DataManager
import uuid
from PIL import Image
import Keyboard

buttonList = []
addImage = ctk.CTkImage(dark_image=Image.open(config.path("images", "add.png")), size=(22, 22))
class KeybindSelector(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master,fg_color="transparent")
        self.elements = []
        self.listElement()
        
         #UUID 저장

    def refresh(self):
        global buttonList
        for element in self.elements:
            element[0].destroy()
            element[1].destroy()
        for keymap in sum(buttonList, []):
            if keymap.winfo_exists(): 
                keymap.destroy()
        DataManager.eegData.clear()
        DataManager.eegData.extend(DataManager.reload())
        
        for i in DataManager.eegData:
            if i not in DataManager.keybindMap.keys():
                DataManager.keybindMap[i] = []

        self.elements.clear()
        buttonList.clear()
        self.listElement()
        
    def listElement(self):
        global buttonList
        for index, file in enumerate(DataManager.eegData):
            keylabel = ctk.CTkButton(master=self, text=file, font=("맑은 고딕", 20), width=130, fg_color="#292929", corner_radius=7, hover=False, anchor="center",)# border_width=0.5, border_color="#d4d4d4")
            keylabel.grid(row=index, column=0, pady=6, padx=(10, 4), sticky="w")
            columnCounter = 1
            _buttonList = []
            for keymap in DataManager.keybindMap.get(file, []):
                keymapButton = KeyButton(self, file, keymap)
                keymapButton.bind("<Button-3>", command=(lambda _, file=file, keymapButton=keymapButton: self.keyRemove(file, keymapButton)))
                keymapButton.grid(row=index, column=columnCounter, pady=6, padx=3)
                columnCounter += 1
                _buttonList.append(keymapButton)
            buttonList.append(_buttonList)
            addButton = ctk.CTkLabel(master=self, image=addImage, text="", corner_radius=7, fg_color="#292929", width=20, height=35)
            addButton.bind(sequence="<Button-1>", command=lambda _, file=file: self.addButtonFunc(file))
            addButton.grid(row=index, column=columnCounter, pady=6, padx=2)

            self.elements.append((keylabel, addButton))
    def keyRemove(self, file, keymapButton):
        print("[LOG: LIST] "+str(list(map(lambda x: str(x.id)[:10], buttonList[0]))))
        print("[LOG: TEXT] "+str(buttonList[0][-1].key))
        print("[LOG: ID] "+str(keymapButton.id))
        print("[LOG: INDEX] "+str(keymapButton.getIndex()))
        del (DataManager.keybindMap[file])[keymapButton.getIndex()]
        print("[LOG: KEYMAP] "+str(DataManager.keybindMap))
        self.refresh()

    def addButtonFunc(self, file):
        if config.disabled: return
        keymaps = DataManager.keybindMap.get(file, None)
        if keymaps:
            keymaps.append(None)
        else:
            DataManager.keybindMap[file] = [None]

        self.refresh()

clickedButton = ""

class KeyButton(ctk.CTkButton):
    def __init__(self, master, bindFile: str, key: str):
        self.bindFile = bindFile
        self.key = key
        super().__init__(
            master=master, 
            text=self.key, 
            font=("맑은 고딕", 18),
            border_width=1,
            border_color="#d4d4d4",
            fg_color="#292929",
            width=35,
            height=32
        )
        
        self.id = uuid.uuid4()

    def _clicked(self, event):
        global clickedButton
        if config.disabled: 
            return
        else: 
            config.toggleAbility()
            
        super()._clicked(event)
        if clickedButton != self.id:
            self.configure(fg_color="#206AA4")
            clickedButton = self.id
            index = self.getIndex()
            Keyboard.listenKeyboard(self.bindFile, index)
        else:
            clickedButton = ""
            self.reloadColor()
        config.toggleAbility()
    def getIndex(self):
        for buttons in buttonList:
            idList = list(map(lambda x: x.id, buttons))
            if self.id in idList:
                return idList.index(self.id)

    def reloadColor(self):
        global buttonList
        for button in sum(buttonList, []):
            if button.id != clickedButton:
                button.configure(fg_color="#292929")



        # original_size = len(self.elements)
        # if original_size < len(eegData):
        #     for index, file in enumerate(eegData[original_size:]):
        #         keylabel = ctk.CTkButton(master=self, text=file, font=("맑은 고딕", 16), width=120, fg_color="#292929", corner_radius=7, hover=False, border_width=1, border_color="#d4d4d4", anchor="w")
        #         keylabel.grid(row=index+original_size, column=0, pady=5, padx=(7, 3), sticky="w")
            
        #         keymap = ctk.CTkSegmentedButton(master=self, values=[], fg_color="#212121", selected_color="#206AA4", unselected_color="#1D1E1E", text_color="#ffffff")
        #         keymap.grid(row=index+original_size, column=1, pady=5)
        #         for button in keymap._buttons_dict.values():
        #             button.configure(border_width=1, border_color="#d4d4d4")
        #         self.elements.append((file, keylabel, keymap))
        # else:
        #     for (file, keylabel, keymap) in [x for x in self.elements if x[0] not in eegData]:
        #         self.elements.remove((file, keylabel, keymap))
        #         keylabel.destroy()
        #         keymap.destroy()
        #         del keybindMap[file]
        #     for index, (_, keylabel, keymap) in enumerate(self.elements):
        #         keylabel.grid_configure(row=index)
        #         keymap.grid_configure(row=index)        