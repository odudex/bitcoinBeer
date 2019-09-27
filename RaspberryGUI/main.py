#!/usr/bin/env python

"""main.py: Main BitBeer GUI file"""

__author__      = "Eduardo Schoenknecht"
__credits__ = ["Eduardo Schoenknecht", "Felipe Borges Alves", "Paulo Eduardo Alves"]

from tkinter import *
import time
import pyqrcode
import threading
import requests
import json
import urllib3

# disable self-signed warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()

BASE_URL = "https://md5hash.ddns.net:8080/LndPayRequest/v1"
HTTP_OK = 200

debugConfig = True #True to allow debug and configurations
rPi = False #True to activate raspberry pi IOs, false to run the GUI on other platforms

beerName = "Pilsen"
LiterPriceBRL = 0.01 # 1 cent of Brazilian Real
flow_calibration = 1000 #pulses/Liter
BTC_BRL = 35000
SAT_BRL = BTC_BRL*0.00000001
BTC_USD = 8000

paymentRequest = "Imposto eh roubo"
paymentId = 0
payment_amount = 0
dump_volume = 0
flow_counter = 0
dump_pulses = 0
timeout = 0


def requestPayment(amount, currency):
    data = {}
    data["apikey"] = "bitcoinbeer"
    data["amount"] = amount
    data["currency"] = currency

    try:
        response = requests.post(BASE_URL + "/paymentrequests", json.dumps(data), verify="lndpayrequest.crt",
                                 timeout=(3, 27))
    except requests.exceptions.Timeout:
        print("Timeout occurred")
        log.insert(0.0, "Request timout ocurred\n")
    if response.status_code != HTTP_OK:
        print("Error request payment")
        log.insert(0.0, "Request error ocurred\n")

    data = json.loads(response.text)
    return data["paymentId"], data["paymentRequest"]


def requestPaymentSat(amount):
    return requestPayment(amount, "sat")


def requestPaymentBrl(amount):
    return requestPayment(amount, "BRL")


def requestPaymentUsdl(amount):
    return requestPayment(amount, "USD")


def isInvoicePaid(paymentId):
    response = requests.get(BASE_URL + "/paymentstatus/" + paymentId, verify="lndpayrequest.crt")
    if response.status_code != HTTP_OK:
        print("Error checking payment status")
        log.insert(0.0, "Error checking payment status\n")
        exit()

    data = json.loads(response.text)
    return bool(data["paid"])

def handleFlow(pin):
    global flow_counter
    if pin == FlowSensor:
        flow_counter += 1

if rPi:
    Valvula = 40 #pin number
    FlowSensor = 11
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(Valvula, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FlowSensor, GPIO.IN)
    GPIO.add_event_detect(FlowSensor, GPIO.BOTH, handleFlow)

def cleanIO():
    if rPi:
        GPIO.cleanup()

def CancelBuy():
    if rPi:
        GPIO.output(Valvula, GPIO.LOW)
    frameRequestInvoice.grid_remove()
    frameQRcode.grid_remove()
    frameDump.grid_remove()

def RequestInvoiceDaemon():
    global paymentRequest
    global paymentId
    paymentId, paymentRequest = requestPaymentSat(payment_amount)
    log.insert(0.0, "Lightning payment request: " + paymentRequest + "\n")
    PostInvoice()

def RequestInvoice300():
    global dump_volume
    dump_volume = 0.3
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
    payment_amount = LiterPriceBRL * dump_volume  # payment in BRL
    payment_amount /= SAT_BRL  # payment in Satoshis
    payment_amount = int(payment_amount) # payment in Satoshis(integer)
    frameRequestInvoice.grid()
    log.insert(0.0, "Requesting " + str(payment_amount) + " satoshis...\n")
    requestInvoiceThread = threading.Thread(target=RequestInvoiceDaemon)
    requestInvoiceThread.daemon = True
    requestInvoiceThread.start()

def PostInvoice():
    global timeout
    timeout = 10  # 10*3s ->30.0seconds
    if paymentId:
        code = pyqrcode.create(paymentRequest, error='M')
        code_xbm = code.xbm(scale=5)
        code_bmp = BitmapImage(data=code_xbm)
        code_bmp.config(background="white")
        labelQR['image'] = code_bmp
        frameQRcode.grid()
        paid = False
        while timeout and not paid:
            paid = isInvoicePaid(paymentId)
            if paid:
                log.insert(0.0, "Payment received!\n")
            else:
                log.insert(0.0, "Payment not received. Retrying\n")
            time.sleep(3)
            timeout -= 1
        if timeout:
            Dump()
        else:
            log.insert(0.0, "Payment timeout\n")
    else:
        log.insert(0.0, "Invoice not received!\n")

def DumpControl():
    global timeout
    timeout = 300  # 30.0seconds
    dump_pulses = dump_volume*flow_calibration
    dump_pulses = int(dump_pulses) #pulses from flowmeter allowed
    while(timeout and flow_counter<dump_pulses):
        timeout -= 1
        label_flow_counter['text'] = str(flow_counter)+"ml"
        label_timeout['text'] = "Timeout: " + str(int(timeout/10)) + "s"
        time.sleep(0.1)
    if not timeout:
        log.insert(0.0, "Pour timeout\n")
    CancelBuy()

def OpenValve():
    if rPi:
        GPIO.output(Valvula, GPIO.HIGH)  # open valve

def Dump():
    global flow_counter
    flow_counter = 0
    frameDump.grid()
    dumpControlThread = threading.Thread(target=DumpControl)
    dumpControlThread.daemon = True
    dumpControlThread.start()
    OpenValve()

def ShowConfig():
    frameConfig.grid()

def Prime1s():
    if rPi:
        GPIO.output(Valvula, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(Valvula, GPIO.LOW)
    log.insert(0.0, "Valve opened for 1 second\n")

def QuitConfig():
    frameConfig.grid_remove()

def Exit():
    if rPi:
        cleanIO()
    sys.exit()

#GUI
root = Tk()
#GUI appearance
root.wm_title("BitBeer")
root.minsize(width=480, height=600)
root.option_add("*Foreground", "gold")
root.option_add("*Background", 'black')
root.option_add("*Button*Font", "Calibri 26 bold")
root.attributes("-fullscreen", False)

#GUI constructors
frameInfo = Frame(root)
frameInfo.grid(row=0, column=0, sticky=N+S+W+E)
labelBeer = Label(frameInfo, text=str(beerName)+" ->  R$"+str(LiterPriceBRL)+"/Litro", font=('Calibri', 20, 'bold'), fg='gold')
labelInfo = Label(frameInfo, text="                 1 Bitcoin = R$"+str(BTC_BRL)+" = US$"+\
                    str(BTC_USD), font=('Calibri', 20, 'bold'), fg='gold')
labelBeer.pack(side=LEFT)
labelInfo.pack(side=LEFT)
frameDoses = Frame(root)
frameDoses.grid(row=1, column=0, sticky=N+S+W+E)
buttonsWidth = 20
buttonsHeight = 2
Ypads = (0, 30)
Xpads = 100
SmallDoseButton = Button(frameDoses, text="Chopinho (300ml)", command=RequestInvoice300, highlightcolor='black',
                         width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
SmallDoseButton.pack(side=TOP, pady=Ypads, padx=Xpads)
MediumDoseButton = Button(frameDoses, text="Paint (568ml)", command=RequestInvoice568, highlightcolor='black',
                         width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
MediumDoseButton.pack(side=TOP, pady=Ypads, padx=Xpads)
HighDoseButton = Button(frameDoses, text="Oktoberfest (1L)", command=RequestInvoice1000, highlightcolor='black',
                         width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
HighDoseButton.pack(side=TOP, pady=Ypads, padx=Xpads)

#request Invoice Frame
frameRequestInvoice = Frame(root)
label = Label(frameRequestInvoice, text="Solicitando Invoice...", font=('Calibri', 20, 'bold'))
label.pack()
frameRequestInvoice.grid(row=0, rowspan=2, column=0, sticky=N+S+W+E)
frameRequestInvoice.grid_remove()

#QRCode
code = pyqrcode.create(paymentRequest,  error='M')
code_xbm = code.xbm(scale=5)
code_bmp = BitmapImage(data=code_xbm)
code_bmp.config(background="white")
frameQRcode = Frame(root)
labelQR = Label(frameQRcode, image=code_bmp)
labelQR.pack(side=TOP)
cancelQR = Button(frameQRcode, text="Cancelar compra", command=CancelBuy, highlightcolor='black',
       width=buttonsWidth, height=1, activebackground='gold', activeforeground='black')
cancelQR.pack(side=TOP)
frameQRcode.grid(row=0, rowspan=2, column=0, sticky=N+S+W+E)
frameQRcode.grid_remove()

#Dump
frameDump = Frame(root)
labelDumping = Label(frameDump, text="Servindo...", font=('Calibri', 20, 'bold'))
labelDumping.pack(side=TOP)
label_flow_counter = Label(frameDump, text="0", font=('Calibri', 20, 'bold'))
label_flow_counter.pack(side=TOP)
label_timeout = Label(frameDump, text="10", font=('Calibri', 10, 'bold'))
label_timeout.pack(side=TOP, pady=50)
frameDump.grid(row=0, rowspan=2, column=0, sticky=N+S+W+E)
frameDump.grid_remove()

if debugConfig:
    #GUI debug
    frameLog = Frame(root)
    frameLog.grid(row=2, column=0, sticky=N+S+W+E)
    labelLog = Label(frameLog, text="Log: ").pack(side=TOP)
    log = Text(frameLog, width=40, takefocus=0, highlightthickness=0)
    log.tag_configure('alert', foreground='red', font=("Calibri", 10))
    log.pack(side=TOP, expand=YES, fill=BOTH)

    skipRInvoiceButton = Button(frameRequestInvoice, text="Pular(debug)", command=PostInvoice, highlightcolor='black',
                             width=buttonsWidth, height=1, activebackground='gold', activeforeground='black')
    skipRInvoiceButton.pack(side=TOP)
    skipPayButton = Button(frameQRcode, text="Pular(debug)", command=Dump, highlightcolor='black',
                                width=buttonsWidth, height=1, activebackground='gold', activeforeground='black')
    skipPayButton.pack(side=TOP)

    frameConfigButton = Frame(root)
    frameConfigButton.grid(row=3, column=0, sticky=N + S + W + E)
    configButton = Button(frameConfigButton, text="Configs", command=ShowConfig, highlightcolor='black',
                          activebackground='gold', activeforeground='black', font="Calibri 20 bold")
    configButton.pack(side=LEFT)
    exitButton = Button(frameConfigButton, text="Sair", command=Exit, highlightcolor='black',
                        activebackground='gold', activeforeground='black', font="Calibri 20 bold")
    exitButton.pack(side=LEFT, padx=30)

    #Gui config
    frameConfig = Frame(root)
    frameConfig.grid(row=1, column=0, sticky=N+S+W+E)
    PrimeButton = Button(frameConfig, text="Abrir 1s", command=Prime1s, highlightcolor='black',
                             width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
    PrimeButton.pack(side=TOP)
    QuitConfigButton = Button(frameConfig, text="Voltar", command=QuitConfig, highlightcolor='black',
                             width=buttonsWidth, height=buttonsHeight, activebackground='gold', activeforeground='black')
    QuitConfigButton.pack(side=TOP)
    frameConfig.grid_remove()

Grid.columnconfigure(root, 0, weight=1)
Grid.columnconfigure(root, 1, weight=1)
Grid.rowconfigure(root, 0, weight=1)

root.after(2000, lambda: root.focus_force())
root.mainloop()
