# bitBeer
Implementation of lightning network payment activated beer faucet

This project aims to create a beer faucet that can pour a certain amount of beer bought with Bitcoins using a lightning network payment.

# What it Does
An user will select the wished beer amount using a touch display. A QR code invoice will be presented. After the invoice is payed, a valve opens and allows user to pour beer until a flow meter detects the amount bought flowed through the faucet.

# How it Does
A GUI was created in python’s tkinter, it runs on a raspberry pi, connected to a touch screen display, a valve and a flow meter.
The payments are managed by an external payment server, running full nodes of Bitcoin and Lightning.
