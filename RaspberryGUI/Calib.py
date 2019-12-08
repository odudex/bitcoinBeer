
"""Calib.py: Calibration GUI file"""

__author__      = "Eduardo Schoenknecht"
__credits__ = ["Eduardo Schoenknecht", "Felipe Borges Alves", "Paulo Eduardo Alves"]

from tkinter import *
import tkinter.messagebox as mbox
import Pi

calib_volume = 0
flow_calibration = 0
pre_calibration = 0

class CalibWindow(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.wm_title("Calibration")
        self.transient(parent)
        self.parent = parent
        self.geometry("600x600+0+0")
        self.calib_box()
        self.Backbox()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.wait_window(self)

    def calib_box(self):
        box = Frame(self)
        label_calib = Label(box, text="Pour, than\ninform precisely poured volume:").pack(side=TOP, pady=(10, 0))
        label_volume = Label(box, text="Volume(ml): ").pack(side=LEFT)
        self.entryVolume = Entry(box, width=10, font=('Calibri', 16, 'bold'), fg='black', bg="#139deb")
        self.entryVolume.insert(0, calib_volume)
        self.entryVolume.pack(side=LEFT, padx=(5, 50))
        self.label_pulses = Label(box, text="0")
        self.label_pulses.pack(side=LEFT)
        self.label_pulses['text'] = "Pulses: " + str(Pi.flow_counter)
        box.grid(row=0, column=0, sticky=N + S + W + E)

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def calc_calib(self):
        global calib_volume
        calib_volume = 0
        try:
            calib_volume = int(self.entryVolume.get())
        except:
            mbox.showerror(title="Invalid Calibration",
                           message="Integers only")
        if calib_volume:
            self.calc_box()

    def refresh_pulses(self):
        self.label_pulses['text'] = "Pulses: " + str(Pi.flow_counter)

    def set_calibration(self):
        global flow_calibration
        global pre_calibration
        flow_calibration = pre_calibration
        self.cancel()

    def Backbox(self):
        box = Frame(self)
        w = Button(box, text="Back", width=5, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=20)
        w = Button(box, text="Calculate", width=9, command=self.calc_calib)
        w.pack(side=LEFT, padx=5)
        w = Button(box, text="Pulses", width=6, command=self.refresh_pulses)
        w.pack(side=LEFT, padx=5)
        self.bind("<Escape>", self.cancel)
        box.grid(row=1, column=0, sticky=N + S + W + E)

    def calc_box(self):
        global calib_volume
        global pre_calibration
        pre_calibration = Pi.flow_counter
        pre_calibration *= 1000 #input was in ml
        pre_calibration /= calib_volume
        pre_calibration = int(pre_calibration)
        box = Frame(self)
        calib_text = "Pulses/Liter: " + str(pre_calibration)
        label_calib = Label(box, text=calib_text).pack(side=TOP)
        w = Button(box, text="Use", width=6, command=self.set_calibration)
        w.pack(side=LEFT, padx=5, pady=20)
        w = Button(box, text="Discard", width=8, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=20)
        box.grid(row=0, column=0, rowspan=2, sticky=N + S + W + E)
