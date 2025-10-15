from functools import partial
from muselsl import list_muses, stream
from pylsl import StreamInlet, resolve_streams, resolve_byprop
import threading
from config import path
import asyncio
import config
import csv
from queue import Queue
import numpy as np
import AiFilter
import os
from pyriemann.estimation import Covariances
import AiProcess as ml
import EEGNet
from Dialog import RecordSelectDialog
import time

EEG_QUEUE = Queue(800)
BUFFER = []

def clearQueue(queue: Queue):
    while not queue.empty():
        queue.get()

def learn(): #인공지능 학습
    if not config.disabled:
        config.toggleAbility()
        ml.train()
        config.toggleAbility()

isRunning = False

def record(frame):
    if not config.disabled:
        config.toggleAbility()
        frame.grid_columnconfigure((0,2,4), weight=1)  # 왼쪽 공백
        frame.grid_columnconfigure((1,3), weight=0)
        frame.learnButton.destroy()
        frame.runButton.destroy()
        frame.recordButton.destroy()
        recordingThread = threading.Thread(target=recordEEG, daemon=True) #기록 쓰레드 실행
        recordingThread.start()
        pauseButton = config.buttonGenerate(master=frame, text="일시중지", row=0, column=1, full=True) #일시중지 버튼 생성
        pauseButton.configure(command=lambda: pause(pauseButton))
        cancelButton = config.buttonGenerate(master=frame, text="취소", row=0, column=3, full=True)
        cancelButton.configure(command=cancel)
        config.cancelButton = cancelButton
        config.pauseButton = pauseButton

def hamsterForward():
    thread = threading.Thread(target=monitor_blink, daemon=True)
    thread.start()

    return thread

def monitor_blink():
    global isRunning
    while isRunning:
        if len(EEG_QUEUE.queue) >= 256:
            # 최근 window_size 샘플 가져오기
            window = list(EEG_QUEUE.queue)[-256:]
            # (Samples, Channels) -> (Channels, Samples)
            window = np.array(window).T
            blink = AiFilter.detect_blink(window)
            print(blink)
            if blink:
                config.app.after(0,config.app.controlPanel.blink())
            
        time.sleep(1)


def prediction():
    global isRunning
    threshold = 0.8  # 확률 기준
    lock = threading.Lock()
    
    while isRunning:
        with lock:
            if len(list(EEG_QUEUE.queue)) >= ml.Samples:
                window = np.array(list(EEG_QUEUE.queue)[-ml.Samples:])  # (Samples, Chans)
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
                X_input = np.expand_dims(processed_window, axis=0)

                # 6. Logistic Regression 예측
                probs = ml.pipeline.predict_proba(X_input)
                max_prob = np.max(probs)
                pred_class = np.argmax(probs)
                print(str(pred_class)+" "+str(np.round(probs, 2)))
                if max_prob > threshold:
                    # print(str(pred_class)+" "+str(np.round(probs, 2)))
                    config.app.after(0, partial(config.app.controlPanel.activate, pred_class))
        time.sleep(1)
    
# def prediction():
#     global isRunning
#     threshold = 0.95  # 확률 기준
#     lock = threading.Lock()
    
#     while isRunning:
#         with lock:
#             if len(list(EEG_QUEUE.queue)) >= EEGNet.Samples:
#                 window = np.array(list(EEG_QUEUE.queue)[-EEGNet.Samples:])  # (Samples, Chans)

#                 # 1. 필터링
#                 filtered = np.zeros_like(window)
#                 for ch in range(window.shape[1]):
#                     filtered[:, ch] = AiFilter.filterEEG(window[:, ch])

#                 # 2. baseline 제거
#                 filtered -= EEGNet.baseline_mean

#                 # 3. 정규화
#                 filtered = (filtered - filtered.mean(axis=0, keepdims=True)) / (filtered.std(axis=0, keepdims=True) + 1e-6)

#                 # 4. shape 변환 (Chans, Samples, 1)
#                 processed_window = filtered.T[np.newaxis, ..., np.newaxis]  # (1, Chans, Samples, 1)

#                 # 5. EEGNet 예측
#                 probs = EEGNet.model.predict(processed_window)[0]  # softmax 확률
#                 max_prob = np.max(probs)

#                 if max_prob > threshold:
#                     pred_class = np.argmax(probs)
#                     print(np.round(probs, 2))
#                     config.app.after(0, partial(config.app.controlPanel.activate, pred_class))
#         time.sleep(0.5)



def run(frame): 
    global isRunning
    if not config.disabled:
        isRunning = True
        config.toggleAbility()
        runningThread = threading.Thread(target=prediction, daemon=True)
        runningThread.start()

        frame.runButton.destroy()
        frame.learnButton.destroy()
        frame.recordButton.destroy()

        stopButton = config.buttonGenerate(master=frame, text="종료", row=0, column=0, columnspan=3)
        stopButton.configure(command=partial(stopRunning, stopButton, frame))

        hamsterForward()

def stopRunning(button, frame):
    global isRunning
    isRunning = False
    button.destroy()

    frame.grid_columnconfigure((0,1,2), weight=1)
    frame.grid_columnconfigure((3,4), weight=0)

    frame.recordButton = config.buttonGenerate(master=frame, text="기록", row=0, column=0)
    frame.recordButton.configure(command=partial(record, frame))
    frame.learnButton = config.buttonGenerate(master=frame, text="학습", row=0, column=1)
    frame.learnButton.configure(command=learn)
    frame.runButton = config.buttonGenerate(master=frame, text="실행", row=0, column=2)
    frame.runButton.configure(command=partial(run, frame))

    config.app.controlPanel.deactivate()

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

def cancel():
    global progressBar
    if not isRecorded:
        return
    pauseEvent.clear()
    progressBar.cancel()
    config.pauseButton.destroy()
    config.cancelButton.destroy()
    config.app.buttonFrame

    config.app.buttonFrame.grid_columnconfigure((0,1,2), weight=1)
    config.app.buttonFrame.grid_columnconfigure((3,4), weight=0)
    config.app.buttonFrame.recordButton = config.buttonGenerate(master=config.app.buttonFrame, text="기록", row=0, column=0)
    config.app.buttonFrame.recordButton.configure(command=partial(record, config.app.buttonFrame))
    config.app.buttonFrame.learnButton = config.buttonGenerate(master=config.app.buttonFrame, text="학습", row=0, column=1)
    config.app.buttonFrame.learnButton.configure(command=learn)
    config.app.buttonFrame.runButton = config.buttonGenerate(master=config.app.buttonFrame, text="실행", row=0, column=2)
    config.app.buttonFrame.runButton.configure(command=partial(run, config.app.buttonFrame))

    config.toggleAbility()

def terminate():
    global pauseEvent, BUFFER, isRecorded
    isRecorded = False
    pauseEvent.clear()

    dialog = RecordSelectDialog()
    dialog.focus()
    dialog.grab_set()
    dialog.wait_window()

    try:
        fileName = dialog.getData()
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
        config.pauseButton.destroy()
        config.cancelButton.destroy()
        config.app.buttonFrame.grid_columnconfigure((0,1,2), weight=1)
        config.app.buttonFrame.grid_columnconfigure((3,4), weight=0)
        config.app.buttonFrame.recordButton = config.buttonGenerate(master=config.app.buttonFrame, text="기록", row=0, column=0)
        config.app.buttonFrame.recordButton.configure(command=partial(record, config.app.buttonFrame))
        config.app.buttonFrame.learnButton = config.buttonGenerate(master=config.app.buttonFrame, text="학습", row=0, column=1)
        config.app.buttonFrame.learnButton.configure(command=learn)
        config.app.buttonFrame.runButton = config.buttonGenerate(master=config.app.buttonFrame, text="실행", row=0, column=2)
        config.app.buttonFrame.runButton.configure(command=partial(run, config.app.buttonFrame))
        config.toggleAbility()

lslStartEvent = threading.Event()
pauseEvent = threading.Event()
isRecorded = False

# eeg_info = StreamInfo('MuseEEG', 'EEG', 4, 256, 'float32', 'muse')
# # battery_info = StreamInfo('MuseBattery', 'Telemetry', 4, 256, 'float32', 'muse')
# eegOutlet = StreamOutlet(eeg_info)
# # batteryOutlet = StreamOutlet(battery_info)
# def streaming():
#     asyncio.run(BLE_STREAM())

# async def BLE_STREAM():
#     MUSE_ADDRESS = "00:55:DA:B9:36:B8"
#     COMMAND_CHAR = "273e0001-4c4d-454d-96be-f03bac821358"
#     BATTERY_CHAR = "273e000b-4c4d-454d-96be-f03bac821358"
#     SENSORS = ["273e0003-4c4d-454d-96be-f03bac821358", #TP9
#                "273e0004-4c4d-454d-96be-f03bac821358", #AF7
#                "273e0005-4c4d-454d-96be-f03bac821358", #AF8
#                "273e0006-4c4d-454d-96be-f03bac821358", #TP10
#                ]

#     global eeg_info
#     async with BleakClient(MUSE_ADDRESS, timeout=20) as client:
#         buffer = [None, None, None, None]
#         for svc in client.services:
#             print(svc)
#             for char in svc.characteristics:
#                 print(f"{char.uuid} | {char.properties}")
        

#         def telemetryHandler(_, data):
#             print(data)
#             config.app.after(0, config.app.bottomBar.showBattery, int(data[0]))

#         def eegHandler(index, data):
#             value = np.array(config.unpack_12bit_to_int16(data[:2])) * config.SCALE
#             buffer[index] = value
#             print(value)
#             stream()
                
#         def stream():
#             nonlocal buffer
#             if None not in buffer:
#                 eegOutlet.push_sample(np.array(buffer).T, timestamp=time.time())
#                 buffer = [None, None, None, None] 

#         await client.write_gatt_char(COMMAND_CHAR, b'p\x10', response=False)
#         await asyncio.sleep(0.01)
#         await client.write_gatt_char(COMMAND_CHAR, b'h', response=False)
#         await asyncio.sleep(0.01)
#         await client.start_notify(BATTERY_CHAR, telemetryHandler)
#         await asyncio.sleep(0.01)
#         for index, sensor in enumerate(SENSORS):
#             await client.start_notify(sensor, lambda _, data, index=index: eegHandler(index, data))
#             await asyncio.sleep(0.01)

#         lslStartEvent.set()
                
#         while True:
#             await asyncio.sleep(1)


def streaming(): #MUSELSL 송신
    global muse, lslSartEvent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        muse = list_muses()[0]
        lslStartEvent.set()
        stream(muse['address'])
    except Exception as e:
        print("MUSE 연결 안됨")
        print(e)

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
    sample, _ = inlet.pull_sample(1.5)
    if EEG_QUEUE.qsize() > 256:
        config.QA = AiFilter.check_qa(list(EEG_QUEUE.queue)[-256:])
        config.app.bottomBar.showContact()

    if EEG_QUEUE.full():
        EEG_QUEUE.get()
    if (not isRecorded or (isRecorded and not pauseEvent.is_set())) and sample:
        EEG_QUEUE.put(sample[:-1])

    if isRecorded and not pauseEvent.is_set():
        BUFFER.append([ float(data) for data in sample[:-1] ])

def pylslrecv(): #PYLSL 수신
    global inlet, lslStartEvent
    lslStartEvent.wait()

    try:
        lsl = resolve_streams(wait_time=5)
        inlet = StreamInlet(lsl[0])
        while True:
            receiving()
    except Exception as e:
        print(f"[ERR] Muse 연결 오류 \n{e}")
        
sendingThread = threading.Thread(target=streaming, daemon=True)
sendingThread.start()

receivingThread = threading.Thread(target=pylslrecv, daemon=True)
receivingThread.start() 