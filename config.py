import os
import customtkinter as ctk
import time
import winsound

stopped = False # 앱이 꺼졌는가?
disabled = False #작업이 이미 진행중인가?
app = None #메인 앱
pauseButton = None #중단 버튼
cancelButton = None #취소 버튼
isDarkMode = False #다크모드인가?
QA = [False,False,False,False] #접촉 상태 리스트

FONT = ("NanumGothic", 18) #나눔고딕

def path(*args): #파일 path 함수
    return os.path.join(os.getcwd(), *args) 

def toggleAbility(): #disabled 토글
    global disabled
    disabled = not disabled

def buttonGenerate(master, text, row, column, columnspan=1, full=False) -> ctk.CTkButton: #버튼 만들기 함수
    button = ctk.CTkButton(master=master, text=text, font=FONT)
    button.grid(row=row, column=column, padx=15, pady=5, sticky="nsew" if full else "ew", columnspan=columnspan)
    return button

class TimerProgressBar: #기록 진행률 바
    def __init__(self, terminate, duration=30):
        global app
        self.app = app #메인 앱
        self.duration = duration # 30초 타이머
        self.start_time = None #시작 시간
        self._paused = False #중지했는가?
        self._pause_time = None # 중지한 시간
        self._job = None #after 태스크
        self.terminate = terminate #종결 함수

        self.progressbar = app.progress #프로그레스 바
        

    def start(self):
        self.start_time = time.time()
        self.progressbar.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.progressbar.master.update_idletasks() #바로 업데이트
        self.progressbar.set(0.0) #0으로 초기화
        self.update()

    def update(self):
        if self._paused:
            return

        elapsed = time.time() - self.start_time
        if elapsed <= self.duration:
            progress_value = elapsed / self.duration #프로그레스 바 설정
            self.progressbar.set(progress_value)
            self._job = self.progressbar.after(100, self.update)  # 0.1초 단위로 더 부드럽게
        else:
            self.progressbar.set(1.0)
            self.progressbar.grid_forget()
            winsound.Beep(2000, 500)
            self.terminate()

    def cancel(self):
        self.progressbar.set(1.0)
        self.progressbar.grid_forget()
        winsound.Beep(2000, 500)
        if self._job:
            self.progressbar.after_cancel(self._job)
            self._job = None

    def pause(self):
        if not self._paused:
            self._paused = True
            self._pause_time = time.time() #현재 시간 기록
            if self._job:
                self.progressbar.after_cancel(self._job) #진행률 더하기 멈추기
                self._job = None

    def resume(self): #이어서 시작
        if self._paused:
            paused_duration = time.time() - self._pause_time
            self.start_time += paused_duration #시작시간에 중단중 소모된 시간 더하기

            self._paused = False
            self.update()