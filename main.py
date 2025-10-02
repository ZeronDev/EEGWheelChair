import customtkinter as ctk
from KeySelector import KeySelector
from functools import partial
import DataManager
from ButtonFunction import *
import Muse
import EEGGraph
import config

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.geometry("600x800")
        self.wm_minsize(600, 800)
        self.title("브레인 키") 
        self.grid_rowconfigure((0,3), weight=15)
        self.grid_rowconfigure((1,2,4), weight=1)
        self.grid_columnconfigure((0,1), weight=1)
        self.protocol("WM_DELETE_WINDOW", self.onExit)
        
        keySelector = KeySelector(self)
        keySelector.grid(row=0, column=0, sticky="nsew", columnspan=2, padx=20, pady=10)

        learnButton = config.buttonGenerate(master=self, text="학습", row=1, index=0)
        learnButton.configure(command=Muse.learn)
        runButton = config.buttonGenerate(master=self, text="실행", row=1, index=1)
        runButton.configure(command=partial(Muse.run, (learnButton, runButton)))
        
        graph = EEGGraph.EEGGraph(self)
        graph.grid(row=3, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)

        self.progress = ctk.CTkProgressBar(master=self, width=500)

        recordButton = config.buttonGenerate(master=self, text="기록", row=4, index=0, columnspan=2, full=True)
        recordButton.configure(command=partial(Muse.record, recordButton))
    def onExit(self):
        try:
        # with open(code_code_path("data","keybind.pickle"), "wb") as file:
        #     pickle.dump({}, file)
        # stopObserver(self)
            config.stopped = True
            #TODO: Thread 종료시킬 것
            self.quit()
            # self.after_cancel(EEGGraph.afterID)
            DataManager.keyBindWrite()
            
        except:
            pass

ctk.set_default_color_theme("dark-blue")
ctk.set_appearance_mode("Dark")

app = config.app = App()
app.mainloop()