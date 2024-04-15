#!/usr/bin/env python3
#
# Copyright (c) 2024 Meinhard Kissich
# SPDX-License-Identifier: MIT
#
# File:     gamepad.py
# Usage:    Gamepad GUI to connect to Gamepad SystemVerilog model.
#

import os
import tkinter as tk
import socket
import argparse
import logging
import json
import threading
import queue


logger = logging.getLogger(__name__)

class Gamepad(tk.Frame):
    KEY_DEFAULT_COLOR = "lightgray"
    KEY_ACTIVE_COLOR = "yellow"

    MODE_CAPTURE = "capture"
    MODE_TOGGLE = "toggle"

    def __init__(self, parent, socks_connect=False, addr=None, port=1000, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.mode = self.MODE_CAPTURE
        self.rx_incomplete = ""
        self.rx_queue = queue.Queue()
        self.rx_thread = None
        self.stop_event = threading.Event()

        self.main_frame = tk.Frame(self)
        self.main_frame.pack()

        self.keypad_frame = tk.Frame(self.main_frame)
        self.keypad_frame.grid(row=1, column=1, padx=10, pady=10)

        # mode indicator
        self.lbl_mode = tk.Label(self.main_frame, text=self.MODE_CAPTURE, bg="lightgray", width=8)
        self.lbl_mode.grid(row=0, column=0, columnspan=1, padx=5, pady=5)

        # create led indicators
        self.led1 = tk.Label(self.main_frame, text="Led 1", bg="lightgray", width=15)
        self.led1.grid(row=0, column=1, columnspan=1, padx=1, pady=5)

        self.led2 = tk.Label(self.main_frame, text="Led 2", bg="lightgray", width=15)
        self.led2.grid(row=0, column=2, columnspan=1, padx=1, pady=5)

        self.led_map = {'led1': self.led1, 'led2': self.led2}

        # create key indicators
        self.keys = {}
        for key, (row, column) in {'w': (0, 1), 'a': (1, 0), 's': (1, 1), 'd': (1, 2)}.items():
            key_pad = tk.Label(self.keypad_frame, text=key.upper(), bg=self.KEY_DEFAULT_COLOR, width=5, height=2)
            key_pad.grid(row=row, column=column, padx=5, pady=5)
            self.keys[key] = key_pad

        self.keypad_frame.grid_columnconfigure(3, minsize=70)

        for key, (row, column) in {'m': (1, 5), 'k': (0, 6)}.items():
            key_pad = tk.Label(self.keypad_frame, text=key.upper(), bg=self.KEY_DEFAULT_COLOR, width=5, height=2)
            key_pad.grid(row=row, column=column, padx=5, pady=5)
            self.keys[key] = key_pad
            
        self.translate_sensors = {"a": "l", "d": "r", "w": "u", "s": "d", "m": "a", "k": "b"}

        self.keys_map = {key: self.keys[key] for key in self.keys}        
        self.state_sensors = {key: False for key in self.keys_map}
        self.state_actors = {key: False for key in self.led_map}

        self.sock = None
        if socks_connect:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((addr, port))
            logger.info(f"Connected to server: {addr}:{port}")
            self.rx_thread = threading.Thread(target=self.recv_thread, args=(self.sock, self.rx_queue)).start()
            self.recv_state()
 
        self.parent.bind('<KeyPress>', self.handle_keydown)
        self.parent.bind('<KeyRelease>', self.handle_keyup)

    def recv_thread(self, socket, queue):
        print("in thread")
        if self.sock == None:
            return
        while not self.stop_event.is_set():
            data = socket.recv(1024).decode('utf-8')
            queue.put(data)

    def get_translated_sensor_state(self):
        translated = {}
        for key, value in self.state_sensors.items():
            if key in self.translate_sensors:
                new_key = self.translate_sensors[key]
                translated[new_key] = value
            else:
                translated[key] = value
        return translated

    def send_state(self):
        dat = json.dumps(self.get_translated_sensor_state())
        dat = "[gamepad]-" + dat + "\n"
        dat = dat.encode()
        logger.info(f"[gamepad -> srv] {dat}")
        if self.sock == None:
            return
        self.sock.sendall(dat)

    def recv_state(self):
        while not self.rx_queue.empty():
            self.rx_incomplete += self.rx_queue.get()
        
        while "\n" in self.rx_incomplete:
            tmp = self.rx_incomplete.split('\n', 1)
            frame = tmp[0]
            self.rx_incomplete = tmp[1]
            self.handle_received(frame)
        self.after(100, self.recv_state)


    def handle_received(self, frame):
        for key,value in json.loads(frame).items():
            self.led_map[key].config(bg=self.KEY_ACTIVE_COLOR if value else self.KEY_DEFAULT_COLOR)

    def handle_keydown(self, event):
        key = event.keysym

        if key == "space":
            self.mode = self.MODE_CAPTURE if (self.mode == self.MODE_TOGGLE) else self.MODE_TOGGLE
            self.lbl_mode.config(text=self.mode)

        if key in self.keys_map:
            if self.mode == self.MODE_CAPTURE:
                lbl = self.keys_map[key]
                lbl.config(bg=self.KEY_ACTIVE_COLOR)
                self.state_sensors[key] = True
            else:
                self.state_sensors[key] = not self.state_sensors[key]
                lbl = self.keys_map[key]
                lbl.config(bg=self.KEY_ACTIVE_COLOR if self.state_sensors[key] else self.KEY_DEFAULT_COLOR)
            self.send_state() 

    def handle_keyup(self, event):
        key = event.keysym
        if (key in self.keys_map) and (self.mode == self.MODE_CAPTURE):
            lbl = self.keys_map[key]
            lbl.config(bg=self.KEY_DEFAULT_COLOR)
            self.state_sensors[key] = False
            self.send_state()

    def on_closing(self):
        self.stop_event.set()
        if self.sock:
            self.sock.shutdown(2) # SHUT_RDWR
        if self.rx_thread is not None:
            self.rx_thread.join()
        self.parent.destroy()

def main(socks_connect, addr, port):
    os.system('xset r off')
    root = tk.Tk()
    root.title("Gamepad")
    Gamepad(root, socks_connect, addr, port).pack(side="top", fill="both", expand=True)
    root.mainloop()
    os.system('xset r on')

def get_args():
    parser = argparse.ArgumentParser(description="DPI-C Verilog Model Gamepad")
    parser.add_argument("-s", "--server", action="store_true", help="Connect to sockets server")
    parser.add_argument("-a", "--address", action="store", type=str, default="localhost", help="Sockets server address")
    parser.add_argument("-p", "--port", action="store", type=int, default=1080, help="Sockets server port")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )

    main(args.server, args.address, args.port)