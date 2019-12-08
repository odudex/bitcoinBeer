
"""Config.py: Configuration GUI """

__author__      = "Eduardo Schoenknecht"
__credits__ = ["Eduardo Schoenknecht", "Felipe Borges Alves", "Paulo Eduardo Alves"]

from tkinter import *
from tkinter import ttk
from configparser import ConfigParser
import tkinter.messagebox as mbox
import Pi
import Calib

beer_name = "Pilsen"
liter_priceBRL = 0.01  # 1 cent of Brazilian Real
flow_calibration = 3340  # pulses/Liter
BTC_BRL = 33000
SAT_BRL = BTC_BRL*0.00000001
BTC_USD = 8000
live_rates = False


class ConfigWindow(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.wm_title("Settings")
        self.transient(parent)
        self.parent = parent
        self.geometry("600x600+0+0")
        self.beer_box()
        self.CalibBox()
        self.ValveBox()
        self.MoneyBox()
        self.Backbox()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.wait_window(self)

    @staticmethod
    def get_config():
        global beer_name
        global liter_priceBRL
        global flow_calibration
        global BTC_BRL
        global SAT_BRL
        global BTC_USD
        global live_rates
        
        config = ConfigParser()
        config.read('config.beer')
        beer_name = config.get('beer', 'name')
        liter_priceBRL = config.getfloat('beer', 'liter_price_brl')
        flow_calibration = config.getint('calibration', 'flow')
        BTC_BRL = config.getfloat('money', 'btc_brl')
        SAT_BRL = BTC_BRL*0.00000001
        BTC_USD = config.getfloat('money', 'btc_usd')
        if config.get('live', 'use_live_rates') == "True":
            live_rates = True
        else:
            live_rates = False

    def toggle_valve(self):
        if Pi.valve_opened:
            self.valveButton['text'] = "Open Valve"
            Pi.close_valve()
        else:
            self.valveButton['text'] = "Close Valve"
            Pi.open_valve()

    def calc_calib(self):
        global flow_calibration
        Pi.flow_counter = 0
        Calib.CalibWindow(self)
        if Calib.flow_calibration:
            flow_calibration = Calib.flow_calibration
            self.entryPulses.delete(0, END)
            self.entryPulses.insert(0, flow_calibration)


    def set_beer_name(self):
        global beer_name
        beer_name = self.entryName.get()
        
    def set_beer_price(self):
        global liter_priceBRL
        try:
            liter_priceBRL = float(self.entryPrice.get())
        except:
            mbox.showerror(title="Invalid Price",
                           message="Numbers only. Ex: '1.99'")

    def set_calibration(self):
        global flow_calibration
        try:
            flow_calibration = int(self.entryPulses.get())
        except:
            mbox.showerror(title="Invalid calibration",
                           message="Integers only")

    def set_money(self):
        global BTC_BRL
        global BTC_USD
        global live_rates
        try:
            BTC_BRL = float(self.entryBTC_BRL.get())
            BTC_USD = float(self.entryBTC_USD.get())
        except:
            mbox.showerror(title="Invalid Price",
                           message="Numbers only. Ex: '30000.99'")
        if self.comboLive.get() == "Enabled":
            live_rates = True
        else:
            live_rates = False

    def beer_box(self):
        box = Frame(self)
        label_beer = Label(box, text="Beer data:").pack(side=TOP, pady=(10, 0))
        label_name = Label(box, text="Name: ").pack(side=LEFT)
        self.entryName = Entry(box, width=10, font=('Calibri', 16, 'bold'), fg='black', bg="#139deb")
        self.entryName.insert(0, beer_name)
        self.entryName.pack(side=LEFT, padx=(5, 50))



        labelPrice = Label(box,text="Price/L").pack(side=LEFT, padx = (20,0))
        self.entryPrice = Entry(box, width=5, font=('Calibri', 16, 'bold'), fg='black', bg="#139deb")
        self.entryPrice.insert(0, str(liter_priceBRL))
        self.entryPrice.pack(side=LEFT, padx=5)
        box.grid(row=0, column=0, sticky=N + S + W + E)

    def CalibBox(self):
        box = Frame(self)
        labelCalib = Label(box, text="\nCalibration:").pack(side=TOP, pady=(10, 0))
        labelCalibPulses = Label(box, text="Pulses per liter: ").pack(side=LEFT)
        self.entryPulses = Entry(box, width=6, font=('Calibri', 16, 'bold'), fg='black', bg="#139deb")
        self.entryPulses.insert(0, flow_calibration)
        self.entryPulses.pack(side=LEFT, padx=(5, 20))
        self.calibButton = Button(box, text="Calibrate", width=10, command=self.calc_calib)
        self.calibButton.pack(side=LEFT, padx=5, pady=20)
        box.grid(row=1, column=0, sticky=N + S + W + E)

    def ValveBox(self):
        box = Frame(self)
        self.valveButton = Button(box, text="Open Valve", width=14, command=self.toggle_valve)
        self.valveButton.pack(side=LEFT, padx=5, pady=20)
        box.grid(row=2, column=0, sticky=N + S + W + E)

    def MoneyBox(self):
        box = Frame(self)
        labelMoney = Label(box, text="\nFinance: ").pack(side=TOP, pady=(10, 0))
        labelBTCBRL = Label(box, text="BTC-BRL").pack(side=LEFT)
        self.entryBTC_BRL = Entry(box, width=8, font=('Calibri', 16, 'bold'), fg='black', bg="#139deb")
        self.entryBTC_BRL.insert(0, BTC_BRL)
        self.entryBTC_BRL.pack(side=LEFT, padx=(5,20))
        labelBTCUSD = Label(box, text="BTC-USD").pack(side=LEFT)
        self.entryBTC_USD = Entry(box, width=8, font=('Calibri', 16, 'bold'), fg='black', bg="#139deb")
        self.entryBTC_USD.insert(0, BTC_USD)
        self.entryBTC_USD.pack(side=LEFT, padx=(5,20))

        labelLive = Label(box, text="Live prices").pack(side=TOP)
        self.comboLive = ttk.Combobox(box, width=10, state='readonly')
        self.comboLive['values'] = ("Enabled", "Disabled")
        if live_rates:
            self.comboLive.set("Enabled")
        else:
            self.comboLive.set("Disabled")
        self.comboLive.pack(side=TOP, padx=0)
        box.grid(row=3, column=0, sticky=N + S + W + E)

    def Backbox(self):
        box = Frame(self)
        w = Button(box, text="< Back", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=20)
        w = Button(box, text="Save", width=10, command=self.save)
        w.pack(side=LEFT, padx=5)
        self.bind("<Escape>", self.cancel)
        box.grid(row=4, column=0, sticky=N+S+W+E)

    @staticmethod
    def saveConfig():
        configData = ConfigParser()
        configData["beer"] = {'name': str(beer_name),
                                'liter_price_brl': str(liter_priceBRL)}

        configData["calibration"] = {'flow': flow_calibration}

        configData["money"] = {'btc_brl': str(BTC_BRL),
                               'btc_usd': str(BTC_USD)}

        if live_rates:
            configData["live"] = {'use_live_rates': "True"}
        else:
            configData["live"] = {'use_live_rates': "False"}

        with open('config.beer', 'w') as configfile:
            configData.write(configfile)

    def save(self, event=None):
        self.set_beer_name()
        self.set_beer_price()
        self.set_calibration()
        self.set_money()
        self.saveConfig()
        self.withdraw()
        self.update_idletasks()
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()
