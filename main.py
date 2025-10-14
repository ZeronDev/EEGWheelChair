import customtkinter as ctk
import Muse
import EEGGraph
import config
from BottomBar import BottomBar
from TopBar import TopBar
from ButtonFrame import ButtonFrame
from HamsterControl import HamsterControl

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        #화면 설정
        self.geometry("600x800")
        self.iconbitmap(config.path("images", "LOGO.ico"))
        self.wm_minsize(600, 800)
        self.title("뇌파 휠체어 조종 어플리케이션") 
        
        #그리드 (행/열) 설정
        self.grid_rowconfigure((0,1,2,4,5), weight=0)
        # self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=20)

        self.grid_columnconfigure(0, weight=1)

        #종료 이벤트 바인딩
        self.protocol("WM_DELETE_WINDOW", self.onExit)
        
        #Top Bar
        self.topBar = TopBar(master=self)
        self.topBar.grid(row=0, column=0, sticky="nsew")

        #햄스터봇
        self.controlPanel = HamsterControl(master=self)
        self.controlPanel.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        #버튼프레임
        self.buttonFrame = ButtonFrame(master=self)
        self.buttonFrame.grid(row=2, column=0, sticky="nsew", padx=20)

        #EEG그래프 표시
        graph = EEGGraph.EEGGraph(self)
        graph.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        # Bottom바 표시
        self.bottomBar = BottomBar(master=self, graph=graph, controlPanel=self.controlPanel)
        self.bottomBar.grid(row=5, column=0, sticky="nsew")

        #진행률 바 표시
        self.progress = ctk.CTkProgressBar(master=self, width=500)

    def onExit(self):
        try:
            #EEG 그래프 종료
            config.stopped = True
            self.quit()
        except:
            pass

#CustomTkinter 기본 테마 설정
ctk.set_default_color_theme("dark-blue")
ctk.set_appearance_mode("light")

#앱 시작
app = config.app = App()
app.mainloop()