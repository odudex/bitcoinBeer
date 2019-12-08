#!/usr/bin/env python

"""main.py: Main BitBeer GUI file"""

__author__      = "Eduardo Schoenknecht"
__credits__ = ["Eduardo Schoenknecht", "Felipe Borges Alves", "Paulo Eduardo Alves"]

from tkinter import *
from tkinter import ttk
import time
import pyqrcode
import threading
import subprocess
import tkinter.messagebox as mbox
import os
import Config
import Pi
import Rates
import Lightning


debug_log = True
debug_payments = True  # True to allow debug and configurations

paymentRequest = "Imposto eh roubo"
paymentId = 0
payment_amountBRL = 0
payment_amount = 0
dump_volume = 0
dump_pulses = 0
config_conter = 0
exit_app = False

Pi.init_hardware()

def OpenConfigWindow():
    root.attributes("-fullscreen", False)
    Config.ConfigWindow(root)
    labelBeer["text"] = str(Config.beer_name) + " ->  R$" + str(Config.liter_priceBRL) + "/Litro"
    labelInfo["text"] = "1 BTC = R$" + str(Config.BTC_BRL) + " = US$" + str(Config.BTC_USD)

def CancelBuy():
    Lightning.timeout = 0
    Pi.close_valve()
    frameRequestInvoice.grid_remove()
    frameQRcode.grid_remove()
    frameDump.grid_remove()

def RequestInvoiceDaemon():
    global paymentRequest
    global paymentId
    paymentId, paymentRequest = Lightning.requestPaymentSat(payment_amount)
    log.insert(0.0, "Lightning payment request: " + paymentRequest + "\n")
    PostInvoice()

def RequestInvoice284():
    global dump_volume
    dump_volume = 0.284
    RequestInvoice()

def RequestInvoice568():
    global dump_volume
    dump_volume = 0.568
    RequestInvoice()

def RequestInvoice1000():
    global dump_volume
    dump_volume = 1
    RequestInvoice()

def RequestInvoice():
    global payment_amount
    global payment_amountBRL
    payment_amountBRL = Config.liter_priceBRL * dump_volume  # payment in BRL
    payment_amount = payment_amountBRL/Config.SAT_BRL  # payment in Satoshis
    payment_amount = int(payment_amount) # payment in Satoshis(integer)
    frameRequestInvoice.grid()
    log.insert(0.0, "Requesting " + str(payment_amount) + " satoshis...\n")
    requestInvoiceThread = threading.Thread(target=RequestInvoiceDaemon)
    requestInvoiceThread.daemon = True
    requestInvoiceThread.start()

def PostInvoice():
    Lightning.timeout = 10  # 10*3s ->30.0seconds
    if paymentId:
        code = pyqrcode.create(paymentRequest, error='M')
        code_xbm = code.xbm(scale=5)
        code_bmp = BitmapImage(data=code_xbm)
        code_bmp.config(background="white")
        labelQR['image'] = code_bmp
        frameQRcode.grid()
        paid = False
        labelQRinfo['text'] = "Waiting payment\n R$" + str(round(payment_amountBRL, 2)) + \
                              "   ->  " + str(payment_amount) + "sats"
        while Lightning.timeout and not paid:
            labelTimeoutQR['text'] = "Time out:" + str(Lightning.timeout * 3) + "s"
            Lightning.timeout -= 1
            time.sleep(3)
            paid = Lightning.isInvoicePaid(paymentId)
            if paid:
                log.insert(0.0, "Payment received!\n")
            else:
                log.insert(0.0, "Payment not received. Retrying\n")
        if Lightning.timeout:
            Dump()
        else:
            log.insert(0.0, "Payment timeout\n")
            CancelBuy()
    else:
        log.insert(0.0, "Invoice not received!\n")

def DumpControl():
    Pi.flow_counter = 0
    Lightning.timeout = 600  # 60.0seconds
    dump_pulses = dump_volume*Config.flow_calibration
    dump_pulses = int(dump_pulses) #pulses from flowmeter allowed
    dump_progress_bar['maximum'] = dump_pulses
    dump_progress_bar['value'] = 0
    while(Lightning.timeout and Pi.flow_counter<dump_pulses):
        Lightning.timeout -= 1
        current_volume = Pi.flow_counter * 1000 / Config.flow_calibration
        current_volume = int(current_volume)
        label_flow_counter['text'] = str(current_volume)+"ml"
        dump_progress_bar['value'] = Pi.flow_counter
        label_timeout['text'] = "Timeout: " + str(int(Lightning.timeout/10)) + "s"
        time.sleep(0.1)
    if not Lightning.timeout:
        log.insert(0.0, "Pour timeout\n")
    CancelBuy()

def Dump():
    Pi.flow_counter = 0
    frameDump.grid()
    dumpControlThread = threading.Thread(target=DumpControl)
    dumpControlThread.daemon = True
    dumpControlThread.start()
    Pi.open_valve()

def get_rates():
    while not exit_app:
        Config.BTC_USD = Rates.get_rate_USD()
        Config.BTC_BRL = Rates.get_rate_BRL()
        labelInfo["text"] = "1 BTC = R$" + str(Config.BTC_BRL) + " = $" + str(Config.BTC_USD)
        time.sleep(120) #2 min

def start_live_rates():
    liveRatesThread = threading.Thread(target=get_rates)
    liveRatesThread.daemon = True
    liveRatesThread.start()


if not sys.platform.startswith('win'):
    try:
        openKeyboard = subprocess.Popen(["/usr/local/bin/matchbox-keyboard", "-g", "300x600", "keyboard"])
    except:
        mbox.showerror(title="No keyboard",
                       message="Install matchbox-keyboard")

def enter_config():
    global config_conter
    global openKeyboard
    config_conter += 1
    if config_conter > 5:
        entry_password.delete(0, 'end')
        entry_password.focus()
        root.attributes("-fullscreen", False)
        config_conter = 0
        frameConfig.grid()

def close_keyboard():
    if not sys.platform.startswith('win'):
        try:
            openKeyboard.terminate()
        except:
            pass

def back_config():
    root.attributes("-fullscreen", True)
    frameConfig.grid_remove()

def test_config_password():
    if entry_password.get() == "a":
        OpenConfigWindow()
        Config.ConfigWindow.get_config()
    else:
        log.insert(0.0, "Incorrect Password!\n")

def Exit():
    global exit_app
    exit_app = True
    close_keyboard()
    Pi.cleanIO()
    sys.exit()

def Shutdown():
    os.system("sleep 10s; sudo shutdown -h now")
    Exit()

# GUI
root = Toplevel() #Used Toplevel instead of Tk() to workaround bugs in auto startup with crontab
# GUI appearance
root.wm_title("BitBeer")
root.minsize(width=480, height=600)
root.option_add("*Foreground", "gold")
root.option_add("*Background", 'black')
root.option_add("*Button*Font", "Calibri 30 bold")
root.attributes("-fullscreen", True)

# Configs
Config.ConfigWindow.get_config()

#GUI constructors
frameInfo = Frame(root)
frameInfo.grid(row=0, column=0, sticky=N+S+W+E)
labelBeer = Label(frameInfo, text=str(Config.beer_name)+" ->  R$"+str(Config.liter_priceBRL)+"/Liter", font=('Calibri', 22, 'bold'), fg='gold')
labelBeer.pack(side=TOP, pady=10)
labelInfo = Label(frameInfo, text="1 BTC = R$"+str(Config.BTC_BRL)+" = US$"+\
                    str(Config.BTC_USD), font=('Calibri', 21, 'bold'), fg='gold')
labelInfo.pack(side=TOP)
frameDoses = Frame(root)
frameDoses.grid(row=1, column=0, sticky=N+S+W+E)
buttonsWidth = 20
buttonsHeight = 2
Ypads = (0, 30)
Xpads = 100
logoButton = Button(frameDoses)
logo = PhotoImage(file="BTC.png")
logoButton.config(image=logo, command=enter_config, bg='black', highlightthickness=0)
logoButton.pack(side=TOP, pady=Ypads)
SmallDoseButton = Button(frameDoses, text="Half Pint (284ml)", command=RequestInvoice284, highlightcolor='black',
                         width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
SmallDoseButton.pack(side=TOP, pady=Ypads, padx=Xpads)
MediumDoseButton = Button(frameDoses, text="Pint (568ml)", command=RequestInvoice568, highlightcolor='black',
                         width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
MediumDoseButton.pack(side=TOP, pady=Ypads, padx=Xpads)
HighDoseButton = Button(frameDoses, text="Oktoberfest (1L)", command=RequestInvoice1000, highlightcolor='black',
                         width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
HighDoseButton.pack(side=TOP, pady=Ypads, padx=Xpads)

#Frame Config
frameConfig = Frame(root)
entry_password = Entry(frameConfig, width=6, font=('Calibri', 16, 'bold'), show="*", fg='black', bg="#139deb")
entry_password.pack(side=TOP)
enterConfigButton = Button(frameConfig, text="Settings", width=20, command=test_config_password)
enterConfigButton.pack(side=TOP, pady=(5, 20))
backConfigButton = Button(frameConfig, text="Back", width=20, command=back_config, highlightcolor='black',
                        activebackground='gold', activeforeground='black')
backConfigButton.pack(side=TOP, pady=20)
exitButton = Button(frameConfig, text="Quit", width=20, command=Exit, highlightcolor='black',
                        activebackground='gold', activeforeground='black')
exitButton.pack(side=TOP, pady=20)
shutDownButton = Button(frameConfig, text="Shutdown", width=20, command=Shutdown, highlightcolor='black',
                        activebackground='gold', activeforeground='black')
shutDownButton.pack(side=TOP, pady=20)
frameConfig.grid(row=0, rowspan=2, column=0, sticky=N+S+W+E)
frameConfig.grid_remove()


#Frame Request Invoice
frameRequestInvoice = Frame(root)
label = Label(frameRequestInvoice, text="Requesting Invoice...", font=('Calibri', 20, 'bold'))
label.pack()
frameRequestInvoice.grid(row=0, rowspan=2, column=0, sticky=N+S+W+E)
frameRequestInvoice.grid_remove()

#QRCode
code = pyqrcode.create(paymentRequest,  error='M')
code_xbm = code.xbm(scale=5)
code_bmp = BitmapImage(data=code_xbm)
code_bmp.config(background="white")
frameQRcode = Frame(root)

labelQRinfo = Label(frameQRcode, text="Waiting payment\n R$" +
                                      str(round(payment_amount, 2)), font=('Calibri', 20, 'bold'))
labelQRinfo.pack(side=TOP)
labelQR = Label(frameQRcode, image=code_bmp)
labelQR.pack(side=TOP)
labelTimeoutQR = Label(frameQRcode, text="Time out:" + str(Lightning.timeout*3), font=('Calibri', 12))
labelTimeoutQR.pack(side=TOP)
cancelQR = Button(frameQRcode, text="Cancel Purchase", command=CancelBuy, highlightcolor='black',
       width=buttonsWidth, height=1, activebackground='gold', activeforeground='black')
cancelQR.pack(side=TOP)
frameQRcode.grid(row=0, rowspan=2, column=0, sticky=N+S+W+E)
frameQRcode.grid_remove()

#Dump
frameDump = Frame(root)
labelDumping = Label(frameDump, text="Pouring...", font=('Calibri', 20, 'bold'))
labelDumping.pack(side=TOP)
label_flow_counter = Label(frameDump, text="0", font=('Calibri', 20, 'bold'))
label_flow_counter.pack(side=TOP)
dump_progress_bar = ttk.Progressbar(frameDump, orient="horizontal", length=400, maximum=10, mode="determinate")
dump_progress_bar.pack(side=TOP)
label_timeout = Label(frameDump, text="10", font=('Calibri', 10, 'bold'))
label_timeout.pack(side=TOP, pady=50)
frameDump.grid(row=0, rowspan=2, column=0, sticky=N+S+W+E)
frameDump.grid_remove()

if debug_log:
    # GUI debug
    frameLog = Frame(root)
    frameLog.grid(row=2, column=0, sticky=N + S + W + E)
    labelLog = Label(frameLog, text="Log: ").pack(side=TOP)
    log = Text(frameLog, width=40, height=12, takefocus=0, highlightthickness=0)
    log.tag_configure('alert', foreground='red', font=("Calibri", 10))
    log.pack(side=TOP, expand=YES, fill=BOTH)

if debug_payments:
    skipRInvoiceButton = Button(frameRequestInvoice, text="Bypass(debug)", command=PostInvoice, highlightcolor='black',
                             width=buttonsWidth, height=1, activebackground='gold', activeforeground='black')
    skipRInvoiceButton.pack(side=TOP)
    skipPayButton = Button(frameQRcode, text="Bypass(debug)", command=Dump, highlightcolor='black',
                                width=buttonsWidth, height=1, activebackground='gold', activeforeground='black')
    skipPayButton.pack(side=TOP)

Grid.columnconfigure(root, 0, weight=1)
Grid.columnconfigure(root, 1, weight=1)
Grid.rowconfigure(root, 0, weight=1)

if Config.live_rates:
    start_live_rates()

root.after(2000, lambda: root.focus_force())
root.mainloop()
