import threading
import customtkinter as ctk
import config
from config import path, FONT
import asyncio
from bleak import BleakClient
import Muse

from PIL import Image


class BottomBar(ctk.CTkFrame):
    
    def __init__(self, master, graph, controlPanel):
        super().__init__(master=master)
        self.graph = graph
        self.controlPanel = controlPanel
        self.MUSE_ADDRESS = "00:55:DA:B9:36:B8" # 추후에 확인 예정 TODO
        self.BATTERY_UUID = "00002A19-0000-1000-8000-00805f9b34fb"
        self.batteryIcons = [ctk.CTkImage(light_image=Image.open(path("images", "light", f"battery{counter}.png")), dark_image=Image.open(path("images", "dark", f"battery{counter}.png")), size=(20, 20)) for counter in range(1, 8) ]
        self.batteryLabel = ctk.CTkLabel(master=self,fg_color="transparent", compound="left", image=self.batteryIcons[6], text="0%", font=FONT, padx=5)
        self.contactFrame = ctk.CTkFrame(master=self, width=60, height=15, fg_color="transparent")
        
        self.good = ctk.CTkImage(light_image=Image.open(path("images", "goodContact.png")), dark_image=Image.open(path("images", "goodContact.png")), size=(20,20))
        self.bad = ctk.CTkImage(light_image=Image.open(path("images", "badContact.png")), dark_image=Image.open(path("images", "badContact.png")), size=(20,20))
        self.unknown = ctk.CTkImage(light_image=Image.open(path("images", "unknown.png")), dark_image=Image.open(path("images", "unknown.png")), size=(20,20))

        self.contactList = [ ctk.CTkLabel(master=self.contactFrame, width=15, height=15, image=self.unknown, text="") for _ in range(5) ]
        self.contactFrame.grid(row=0, column=1, padx=10, pady=5)
        for index, element in enumerate(self.contactList):
            element.grid(row=0, column=index)

        self.appearanceModeSwitch = ctk.CTkSwitch(master=self, width=40, height=15, text="다크 모드", command=self.toggleDarkMode, font=FONT)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure((0,1), weight=0)
        self.grid_columnconfigure(2, weight=1)

        self.contactFrame.grid(row=0, column=0, padx=20, pady=5)
        self.batteryLabel.grid(row=0, column=1, padx=10, pady=5)

        self.appearanceModeSwitch.grid(row=0, column=2, padx=10, pady=5)
    
    def showBattery(self, battery):
        imageIndex = abs((battery // 14) - 1)
        self.batteryLabel.configure(text=f"{battery}%", image=self.batteryIcons[imageIndex])
    
    def showContact(self):
        for index, status in enumerate(config.QA):
            if status:
                self.contactList[index].configure(image=self.bad)
            else:                    
                self.contactList[index].configure(image=self.good)


    def toggleDarkMode(self):
        config.isDarkMode = not config.isDarkMode
        ctk.set_appearance_mode("dark" if config.isDarkMode else "light")
        self.graph.changeColor()
        self.controlPanel.changeColor()

    async def receiveBattery(self):
        async with BleakClient(self.MUSE_ADDRESS) as client:
            # services = client.services
            # for service in services:
            #     print(service)
            #     for char in service.characteristics:
            #         print(" ", char)
            # await client.write_gatt_char(self.BATTERY_UUID, bytearray(b's'), response=True)
            
            while True:
                # # battery = await client.start_notify(self.BATTERY_UUID, lambda _, x: print("asdf"))
                # # await asyncio.sleep(30) 
                # # await client.stop_notify(self.BATTERY_UUID)
                # await client.start_notify(self.BATTERY_UUID, lambda x, y: print(x, y))
                
                # # 30초 동안 데이터 수신 대기
                # await asyncio.sleep(30) 

                battery = await client.read_gatt_char(self.BATTERY_UUID)
                print(battery)
                
                # await client.stop_notify(self.BATTERY_UUID)
                config.app.after(0, self.showBattery, int(battery[0]))
                await asyncio.sleep(30)

    def eventLoop(self):
        Muse.lslSartEvent.wait()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.receiveBattery())


    def startReceive(self):
        threading.Thread(target=self.eventLoop, daemon=True).start()
