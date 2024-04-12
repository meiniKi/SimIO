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

logger = logging.getLogger(__name__)

class Gamepad(tk.Frame):
    KEY_DEFAULT_COLOR = "lightgray"
    KEY_ACTIVE_COLOR = "yellow"

    def __init__(self, parent, socks_connect=False, addr=None, port=1000, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.main_frame = tk.Frame(self)
        self.main_frame.pack()

        self.keypad_frame = tk.Frame(self.main_frame)
        self.keypad_frame.grid(row=1, column=0, padx=10, pady=10)

        # create led indicators
        self.led1 = tk.Label(self.main_frame, text="Led 1", bg="lightgray", width=20)
        self.led1.grid(row=0, column=0, columnspan=3, padx=10, pady=5)

        self.led2 = tk.Label(self.main_frame, text="Led 2", bg="lightgray", width=20)
        self.led2.grid(row=0, column=3, columnspan=3, padx=10, pady=5)

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
            logger.info(f"Connecting to server: {addr}:{port}")
        
        self.parent.bind('<KeyPress>', self.handle_keydown)
        self.parent.bind('<KeyRelease>', self.handle_keyup)

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
        if self.sock == None:
            return
        dat = self.client_socket.recv(1024).decode()
        self.state_actors = json.loads(dat)
        self.after(100, self.check_for_data)


    def handle_recv(self):
        pass


    def handle_keydown(self, event):
        key = event.keysym
        if key in self.keys_map:
            lbl = self.keys_map[key]
            lbl.config(bg=self.KEY_ACTIVE_COLOR)
            self.state_sensors[key] = True
            self.send_state()


    def handle_keyup(self, event):
        key = event.keysym
        if key in self.keys_map:
            lbl = self.keys_map[key]
            lbl.config(bg=self.KEY_DEFAULT_COLOR)
            self.state_sensors[key] = False
            self.send_state()


def main(socks_connect, addr, port):
    os.system('xset r off')
    root = tk.Tk()
    root.title("Gamepad")
    Gamepad(root, socks_connect, addr, port).pack(side="top", fill="both", expand=True)
    root.mainloop()


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