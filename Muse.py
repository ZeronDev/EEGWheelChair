from functools import partial
from muselsl import stream, list_muses
from pylsl import StreamInlet, resolve_streams
import threading
from config import path
import asyncio
import time
import config
import csv
from queue import Queue
import numpy as np
from InputDialog import SelectInputDialog
import DataManager
import AiFilter
import torch.nn.functional as F
import torch
from Keyboard import pressKey
import PytorchAi
import os
from pyriemann.estimation import Covariances
import MachinLearning as ml

EEG_QUEUE = Queue(800) #큐
# EEG_DATA = Queue(256)
BUFFER = []

def clearQueue(queue: Queue):
    while not queue.empty():
        queue.get()

def learn(): 
    if not config.disabled:
        config.toggleAbility()
        ml.train() #AI
        config.toggleAbility()
        config.app.progress.grid_forget()

isRunning = False

def record(button):
    button.destroy()
    if not config.disabled and config.other_screen == None:
        config.toggleAbility()
        recordingThread = threading.Thread(target=recordEEG, daemon=True)
        recordingThread.start()
        pauseButton = config.buttonGenerate(master=config.app, text="일시중지", row=4, index=0, columnspan=2)
        pauseButton.configure(command=lambda: pause(pauseButton))
        config.pauseButton = pauseButton


# def prediction():
#     global isRunning
#     threshold = 0.5  # 확률 기준
#     lock = threading.Lock()
    
#     while isRunning:
#         # UI 초기화
#         for x in DataManager.keybindWidget.elements:
#             x[0].configure(fg_color="#292929")
        
#         # 마지막 256 샘플 추출
#         with lock:
#             if len(list(EEG_QUEUE.queue)) >= 256:
#                 window = np.array(list(EEG_QUEUE.queue)[-256:])  # (Samples, Chans)
        
#                 filtered_window = np.zeros_like(window)
#                 for ch in range(window.shape[1]):
#                     filtered_window[:, ch] = AiFilter.filterEEG(window[:, ch])

#                 # 입력 차원 맞추기: (batch, 1, Chans, Samples)
#                 X_tensor = torch.tensor(filtered_window.T[np.newaxis, :, :], dtype=torch.float32).to(PytorchAi.device)
                
#                 # 모델 예측
#                 PytorchAi.model.eval()
#                 with torch.no_grad():
#                     logits = PytorchAi.model(X_tensor)                # (1, n_classes)
#                     probs = F.softmax(logits, dim=1).cpu().numpy()    # 확률로 변환

#                 # 확률 기준 선택
#                 max_prob = np.max(probs)
#                 if max_prob > threshold:
#                     pred_class = np.argmax(probs)
#                     print(probs)
#                     DataManager.keybindWidget.elements[pred_class][0].configure(fg_color="#206AA4")
#                     pressKey(pred_class)

def prediction():
    global isRunning
    threshold = 0.9  # 확률 기준
    lock = threading.Lock()
    while isRunning:
        # UI 초기화
        for x in DataManager.keybindWidget.elements:
            x[0].configure(fg_color="#292929")
        with lock:
            if len(list(EEG_QUEUE.queue)) >= 784:
                window = np.array(list(EEG_QUEUE.queue)[-768:])  # (Samples, Chans)
                # 필터링
                filtered = np.zeros_like(window)
                for ch in range(window.shape[1]):
                    filtered[:, ch] = AiFilter.filterEEG(window[:, ch])
                
                # baseline 제거
                filtered -= ml.baseline_mean
                #정규화
                filtered = (filtered - filtered.mean(axis=0, keepdims=True)) / (filtered.std(axis=0, keepdims=True) + 1e-6)

                # 4. shape 변환 (Chans, Samples)
                processed_window = filtered.T

                # 5. Covariance → Tangent Space → 스케일링
                cov = Covariances().fit_transform(np.expand_dims(processed_window, axis=0))
                X_ts = ml.ts.transform(cov)
                X_scaled = ml.scaler.transform(X_ts)

                # 6. Logistic Regression 예측
                probs = ml.clf.predict_proba(X_scaled)[0]
                max_prob = np.max(probs)

                if max_prob > threshold:
                    pred_class = np.argmax(probs) + 1
                    print(probs)
                    DataManager.keybindWidget.elements[pred_class][0].configure(fg_color="#206AA4")
                    pressKey(pred_class)

    

def run(buttons): 
    global isRunning
    if not config.disabled:
        isRunning = True
        config.toggleAbility()
        runningThread = threading.Thread(target=prediction, daemon=True)
        runningThread.start()

        buttons[0].destroy()
        buttons[1].destroy()

        stopButton = config.buttonGenerate(master=config.app, text="종료", row=1, index=0, columnspan=2)
        stopButton.configure(command=partial(stopRunning, stopButton))


def stopRunning(button):
    global isRunning
    isRunning = False
    button.destroy()

    learnButton = config.buttonGenerate(master=config.app, text="학습", row=1, index=0)
    learnButton.configure(command=learn)
    runButton = config.buttonGenerate(master=config.app, text="실행", row=1, index=1)
    runButton.configure(command=partial(run, (learnButton, runButton)))
    
    for x in DataManager.keybindWidget.elements:
        x[0].configure(fg_color="#292929")

    config.toggleAbility()



def pause(button): 
    global progressBar
    if not isRecorded:
        return
    if pauseEvent.is_set():
        button.configure(text="일시중지")
        progressBar.resume()
        pauseEvent.clear()
    else:
        button.configure(text="재개")
        progressBar.pause()
        pauseEvent.set()#PAUSE event set할 것


def terminate():
    global pauseEvent, BUFFER, isRecorded
    isRecorded = False
    pauseEvent.clear()
    

    config.other_screen = SelectInputDialog("저장할 파일 선택")
    config.other_screen.focus()
    config.other_screen.grab_set()
    config.other_screen.wait_window()

    try:
        fileName = config.other_screen.getData().get()
        count = len(list(filter(lambda files: files.startswith(fileName), os.listdir(path("data")))))
        filePath = path("data", fileName+str(count)+".csv")
        if os.path.getsize(path("data", fileName+".csv")) == 0:
            filePath = path("data", fileName+".csv")
        
        with open(filePath, "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerows(BUFFER[:256*30])
    except Exception as e: print("[terminate] 이미 파일이 열려있거나 예기치 못한 오류\n" + str(e))
    finally:
        BUFFER = []
        config.other_screen = None
        config.pauseButton.destroy()
        recordButton = config.buttonGenerate(master=config.app, text="기록", row=4, index=0, columnspan=2, full=True)
        recordButton.configure(command=partial(record, recordButton))
        config.toggleAbility()
        

muse = None
lslSartEvent = threading.Event()
pauseEvent = threading.Event()
isRecorded = False

def streaming(): #MUSELSL 송신
    global muse, lslSartEvent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        muse = list_muses()[0]
        lslSartEvent.set()
        stream(muse['address'])
    except Exception as e:
        print("MUSE 연결 안됨")
        # print(f"[ERR] Muse Streaming Error Occurred \n{e}")
        # print(e)

progressBar = None

def recordEEG():
    global progressBar
    global terminateEvent, pauseEvent, BUFFER, isRecorded
    clearQueue(EEG_QUEUE)
    isRecorded = True
    progressBar = config.TimerProgressBar(terminate, 30)
    progressBar.start()

inlet = None
def receiving():
    global inlet, pauseEvent,isRecorded
    sample, timestamp = inlet.pull_sample(1.5)
    if EEG_QUEUE.full():
        EEG_QUEUE.get()
    if (not isRecorded or (isRecorded and not pauseEvent.is_set())) and sample:
        EEG_QUEUE.put(sample[:-1])

    if isRecorded and not pauseEvent.is_set():
        BUFFER.append([ float(data) for data in sample[:-1] ])
    # print(EEG_QUEUE.get())

def pylslrecv(): #PYLSL 수신
    global inlet, lslSartEvent
    lslSartEvent.wait()

    try:
        lsl = resolve_streams(5.0)
        inlet = StreamInlet(lsl[0])

        while True:
            receiving()
            #time.sleep(0.1)
    except Exception as e:
        print(f"[ERR] Muse Receiving Error Occurred \n{e}")
        
sendingThread = threading.Thread(target=streaming, daemon=True)
sendingThread.start()

receivingThread = threading.Thread(target=pylslrecv, daemon=True)
receivingThread.start()
#TODO