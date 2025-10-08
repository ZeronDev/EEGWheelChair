import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from Muse import EEG_QUEUE
import threading
import config

# afterID = ""

class EEGGraph(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master)
        self.master = master
        self.fig, self.ax = plt.subplots()

        self.color = "#e5e5e5"
        self.fig.patch.set_facecolor(self.color)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.ax.set_facecolor(self.color)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.lines = []
        self.ax.set_xlim(0, 600)  # 혹은 적당한 데이터 길이
        self.ax.set_ylim(-1500, 1500)
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.set_xticks([]) 
        self.ax.set_yticks([])
        colors = ['r', 'g', 'b', 'y']#['lightcoral','gold','lightskyblue','limegreen', 'violet']
        for x in range(4):
            line, = self.ax.plot([], [], f"{colors[x]}-")
            self.lines.append(line)
        self.updateCanvas()
        self.canvas.get_tk_widget().pack(fill="both",expand=True)

    def changeColor(self):
        self.color = "#292929" if config.isDarkMode else "#e5e5e5"
        self.ax.set_facecolor(self.color)
        self.fig.patch.set_facecolor(self.color)


    def updateCanvas(self):
        try:
            lock = threading.Lock()
            if not EEG_QUEUE.empty():
                for i in range(4):
                    with lock:
                        data = list(map(lambda x: x[i], list(EEG_QUEUE.queue)))
                        self.lines[i].set_data(range(1,len(data)+1), data)
        finally:
            self.canvas.draw()
            if not config.stopped and self.master.winfo_exists():
                # print(stopped)
                self.master.after(100, self.updateCanvas)