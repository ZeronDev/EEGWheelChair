from functools import partial
from muselsl import stream, list_muses
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
        frame.grid_columnconfigure((1,3), weight=0)  # a
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
    threading.Thread(target=monitor_blink, daemon=True)

def monitor_blink():
    while True:
        if not isRunning:
            continue
        if len(EEG_QUEUE.queue) >= 256:
            # 최근 window_size 샘플 가져오기
            window = list(EEG_QUEUE.queue)[-256:]
            # (Samples, Channels) -> (Channels, Samples)
            window = np.array(window).T
            blink = AiFilter.detect_blink(window)
            if blink:
                config.app.controlPanel.blink()
            config.app.controlPanel.forward()
        time.sleep(2000)


def prediction():
    global isRunning
    threshold = 0.95  # 확률 기준
    lock = threading.Lock()
    while isRunning:
        config.app.controlPanel.deactivate()
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
                    config.app.controlPanel.activate(pred_class)

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

def stopRunning(button, frame):
    global isRunning
    isRunning = False
    button.destroy()

    frame.grid_columnconfigure((0,1,2), weight=1)

    frame.recordButton = config.buttonGenerate(master=frame, text="기록", row=0, column=0)
    frame.recordButton.configure(command=partial(record, frame))
    frame.learnButton = config.buttonGenerate(master=frame, text="학습", row=0, column=1)
    frame.learnButton.configure(command=learn)
    frame.runButton = config.buttonGenerate(master=frame, text="실행", row=0, column=2)
    frame.runButton.configure(command=partial(run, frame))

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

    config.app.buttonFrame.grid_columnconfigure((0,1,2), weight=1)
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
        fileName = dialog.getData().get()
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
        config.app.buttonFrame.recordButton = config.buttonGenerate(master=config.app.buttonFrame, text="기록", row=0, column=0)
        config.app.buttonFrame.recordButton.configure(command=partial(record, config.app.buttonFrame))
        config.app.buttonFrame.learnButton = config.buttonGenerate(master=config.app.buttonFrame, text="학습", row=0, column=1)
        config.app.buttonFrame.learnButton.configure(command=learn)
        config.app.buttonFrame.runButton = config.buttonGenerate(master=config.app.buttonFrame, text="실행", row=0, column=2)
        config.app.buttonFrame.runButton.configure(command=partial(run, config.app.buttonFrame))
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
        stream(muse['address'], ['telemetry'])
    except Exception as e:
        print("MUSE 연결 안됨")

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
    global inlet, qa_inlet, pauseEvent,isRecorded
    sample, _ = inlet.pull_sample(1.5)
    if EEG_QUEUE.qsize() > 256:
        config.QA = AiFilter.check_qa(list(EEG_QUEUE.queue)[-256:])

    if EEG_QUEUE.full():
        EEG_QUEUE.get()
    if (not isRecorded or (isRecorded and not pauseEvent.is_set())) and sample:
        EEG_QUEUE.put(sample[:-1])

    if isRecorded and not pauseEvent.is_set():
        BUFFER.append([ float(data) for data in sample[:-1] ])
    # print(EEG_QUEUE.get())

def pylslrecv(): #PYLSL 수신
    global inlet, qa_inlet, lslSartEvent
    lslSartEvent.wait()

    try:
        lsl = resolve_streams(5.0)
        inlet = StreamInlet(lsl[0])
        
        while True:
            receiving()
    except Exception as e:
        print(f"[ERR] Muse 연결 오류 \n{e}")
        
sendingThread = threading.Thread(target=streaming, daemon=True)
sendingThread.start()

receivingThread = threading.Thread(target=pylslrecv, daemon=True)
receivingThread.start()