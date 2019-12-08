
"""Lightning.py: API to connect private payment server"""

__author__      = "Felipe Borges Alves"
__credits__ = ["Eduardo Schoenknecht", "Felipe Borges Alves", "Paulo Eduardo Alves"]


import requests
import json
import urllib3

# disable self-signed warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
urllib3.disable_warnings()

BASE_URL = "https://md5hash.ddns.net:8080/LndPayRequest/v1"
HTTP_OK = 200
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
    if response.status_code != HTTP_OK:
        print("Error request payment")

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
        exit()

    data = json.loads(response.text)
    return bool(data["paid"])
