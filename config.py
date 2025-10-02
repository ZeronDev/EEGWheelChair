import os
import customtkinter as ctk
import time
import winsound

stopped = False
other_screen = None
disabled = False
app = None
pauseButton = None

def path(*args):
    return os.path.join(os.getcwd(), *args)
def toggleAbility():
    global disabled
    disabled = not disabled

def buttonGenerate(master, text, row, index, columnspan=1, full=False) -> ctk.CTkButton:
    button = ctk.CTkButton(master=master, text=text, font=("맑은 고딕", 20))
    button.grid(row=row, column=index, padx=20, pady=10, sticky="nsew" if full else "ew", columnspan=columnspan)
    return button

class TimerProgressBar:
    def __init__(self, terminate, duration=30):
        global app
        self.app = app
        self.duration = duration  # 총 시간 (초)
        self.start_time = None
        self._paused = False
        self._pause_time = None
        self._job = None
        self.terminate = terminate

        self.progressbar = app.progress
        

    def start(self):
        self.start_time = time.time()
        self.progressbar.grid(row=2, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)
        self.progressbar.master.update_idletasks()
        self.progressbar.set(0.0)
        self.update()

    def update(self):
        if self._paused:
            return

        elapsed = time.time() - self.start_time
        if elapsed <= self.duration:
            progress_value = elapsed / self.duration
            self.progressbar.set(progress_value)
            self._job = self.progressbar.after(100, self.update)  # 0.1초 단위로 더 부드럽게
        else:
            self.progressbar.set(1.0)
            self.progressbar.grid_forget()
            winsound.Beep(2000, 500)
            self.terminate()

    def pause(self):
        if not self._paused:
            self._paused = True
            self._pause_time = time.time()
            if self._job:
                self.progressbar.after_cancel(self._job)
                self._job = None

    def resume(self):
        if self._paused:
            paused_duration = time.time() - self._pause_time
            self.start_time += paused_duration

            self._paused = False
            self.update()

class LearningProgressBar:
    def __init__(self, epochs):
        global app
        self.app = app
        self.progressbar = app.progress
        self.counter = 0
        self.epochs = epochs

        self.progressbar.grid(row=2, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)
        self.progressbar.master.update_idletasks()
        self.progressbar.set(0.0)
        self.update()

    def update(self):
        self.counter += 1
        self.progressbar.set(self.counter/self.epochs)

        if self.counter == self.epochs:
            self.end()
    def end(self):
        self.progressbar.set(1.0)
        self.progressbar.grid_forget()
