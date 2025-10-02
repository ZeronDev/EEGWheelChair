import os
from keyboard import press, release
import DataManager
import Keybind
import config
import time

def onPress(event, bind, index):
    DataManager.keybindMap[bind][index] = event.keysym.upper()
    DataManager.keybindWidget.refresh()
    Keybind.clickedButton = ""
    config.app.unbind("<KeyPress>")
def listenKeyboard(bind, index):
    config.app.unbind("<KeyPress>")
    config.app.bind("<KeyPress>", lambda event: onPress(event, bind, index))

def pressKey(class_id):
    keys = set(DataManager.keybindMap[DataManager.eegData[class_id]])
    for key in keys:
        press(key)
    time.sleep(0.1)
    for key in keys:
        release(key)
    