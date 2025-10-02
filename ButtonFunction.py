import Muse
import config
import threading
import numpy as np
import customtkinter as ctk
from InputDialog import SelectInputDialog
from functools import partial
import AiProcess
import csv
import DataManager
from Keyboard import pressKey
import torch
import torch.nn.functional as F
import AiFilter



#def prediction():
#     global isRunning
#     threshold = 0.5
#     lock = threading.Lock()
    
#     while isRunning:
#         for x in DataManager.keybindWidget.elements:
#             x[0].configure(fg_color="#292929")
#         with lock:
#              window = np.array(list(Muse.EEG_QUEUE.queue)[-256:])   # 마지막 256개 샘플만 추출
#         window = window.T[..., np.newaxis]     
#         window = np.expand_dims(window, axis=0) 
#         y_pred = AiProcess.model.predict(window)

#         if np.max(y_pred) > threshold:
#             pred_class = np.argmax(y_pred)
#             DataManager.keybindWidget.elements[pred_class][0].configure(fg_color="#206AA4")
#             pressKey(pred_class)

