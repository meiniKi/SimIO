#!/usr/bin/env python3
#
# Copyright (c) 2024 Meinhard Kissich
# SPDX-License-Identifier: MIT
#
# File:     display.py
# Usage:    Virtual display to show connect to SystemVerilog model.
#

import tkinter as tk
import socket
import argparse
import logging
import json
import threading
import queue
import numpy as np
from PIL import Image, ImageTk, ImageOps

logger = logging.getLogger(__name__)

class DisplayState:
    SRV_INV        = "<inverse>"
    SRV_ONOFF      = "<onoff>"
    SRV_ENTIRE_ON  = "<globon>"
    SRV_FLIP_HOR   = "<flipx>"
    SRV_FLIP_VERT  = "<flipy>"
    SRV_ADR_MODE   = "<adr>"
    
    def __init__(self, w=128, h=64, scale=2) -> None:
        assert w % 8 == 0, "Must be multiple of 8 bits"
        assert h % 8 == 0, "Must be multiple of 8 bits"
        self.bitmap = np.zeros((h, w), dtype=np.uint8)
        self.inverted = False
        self.flipped_x = False
        self.flipped_y = False
        self.off_on    = True
        self.entire_on = False
        self.adr_mode  = "invalid"
        self.w = w
        self.h = h
        self.scale = scale

    def handle_rx(self, json_data):
        frame_dict = json.loads(json_data)
        if not "type" in frame_dict:
            logger.warning("Received invalid json: key 'type' does not exist")
        if frame_dict["type"] == "data":
            self.handle_data(frame_dict)
        elif frame_dict["type"] == "cmd":
            self.handle_cmd(frame_dict)

    def handle_cmd(self, cmd):
        if DisplayState.SRV_INV in cmd:
            self.inverted = cmd[DisplayState.SRV_INV]
        if DisplayState.SRV_ONOFF in cmd:
            self.off_on = cmd[DisplayState.SRV_ONOFF]
        if DisplayState.SRV_ENTIRE_ON in cmd:
            self.entire_on = cmd[DisplayState.SRV_ENTIRE_ON]
        if DisplayState.SRV_FLIP_HOR in cmd:
            self.flipped_x = cmd[DisplayState.SRV_FLIP_HOR]
        if DisplayState.SRV_FLIP_VERT in cmd:
            self.flipped_y = cmd[DisplayState.SRV_FLIP_VERT]
        if DisplayState.SRV_ADR_MODE in cmd:
            self.adr_mode = cmd[DisplayState.SRV_ADR_MODE]

    def handle_data(self, data):
        # TODO other addressing modes
        dx, dy = (1, 0) if self.adr_mode == 'horizontal' else (0, 1)
        x = data["x"]
        y = data["y"]
        for i in range(8):
            bit = (data["data"] & (1 << i)) != 0
            self.bitmap[y % self.h, x % self.w] = 255*bit
            x += dx
            y += dy

    def get_image(self) -> ImageTk.Image:
        # TODO: inverse, on_off, entire on, flip
        image=Image.fromarray(self.bitmap if not self.entire_on else 255*np.zeros((self.h, self.w), dtype=np.uint8))
        image = image.resize((self.w*self.scale,self.h*self.scale))

        if self.inverted:
            image = ImageOps.invert(image)
        if self.flipped_x:
            image = ImageOps.mirror(image)
        if self.flipped_y:
            image = ImageOps.flip(image)
        return image

class Display(tk.Frame):
    SRV_PREFIX     = "[display]-"
    PX_OFF_COLOR = "black"
    PX_ON_COLOR = "lightgray"

    def __init__(self, parent, w=128, h=64, scale=2, socks_connect=False, addr=None, port=1000, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.parent.title("Display")
        self.parent.geometry(f"{w*scale}x{h*scale}")
        self.parent.configure(bg="black")

        self.c = tk.Canvas(self.parent, width=w*scale, heigh=h*scale, bg="black")
        self.c.place(x=0, y=0)
        self.cimage = None

        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.rx_incomplete = ""
        self.rx_queue = queue.Queue()
        self.rx_thread = None
        self.stop_event = threading.Event()

        self.ds = DisplayState(w, h, scale)

        self.main_frame = tk.Frame(self)
        self.main_frame.pack()

        self.sock = None
        if socks_connect:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((addr, port))
            logger.info(f"Connected to server: {addr}:{port}")
            self.rx_thread = threading.Thread(target=self.recv_thread, args=(self.sock, self.rx_queue)).start()
            self.recv_state()

        self.update_image()
 

    def recv_thread(self, socket, queue):
        if self.sock == None:
            return
        while not self.stop_event.is_set():
            data = socket.recv(1024).decode('utf-8')
            queue.put(data)

    def recv_state(self):
        while not self.rx_queue.empty():
            self.rx_incomplete += self.rx_queue.get()
        
        while "\n" in self.rx_incomplete:
            tmp = self.rx_incomplete.split('\n', 1)
            frame = tmp[0]
            self.rx_incomplete = tmp[1]
            logger.info(f"[srv -> display, frame] {frame}")
            self.handle_received(frame)
        self.after(100, self.recv_state)


    def handle_received(self, frame):
        if not frame.startswith(Display.SRV_PREFIX):
            return
        frame = frame.removeprefix(Display.SRV_PREFIX)
        self.ds.handle_rx(frame)
        self.update_image()

    def update_image(self):
        img = self.ds.get_image()
        self.cimage = ImageTk.PhotoImage(image=img)
        self.c.create_image(0, 0, anchor="nw", image=self.cimage)

    def on_closing(self):
        self.stop_event.set()
        if self.sock:
            self.sock.shutdown(2) # SHUT_RDWR
        if self.rx_thread is not None:
            self.rx_thread.join()
        self.parent.destroy()


def main(socks_connect, addr, port, width, height, scale):
    root = tk.Tk()
    Display(root, width, height, scale, socks_connect, addr, port).pack(side="top", fill="both", expand=True)
    root.mainloop()

def get_args():
    parser = argparse.ArgumentParser(description="DPI-C Verilog Model Gamepad")
    parser.add_argument("-s", "--server", action="store_true", help="Connect to sockets server")
    parser.add_argument("-a", "--address", action="store", type=str, default="localhost", help="Sockets server address")
    parser.add_argument("-p", "--port", action="store", type=int, default=1080, help="Sockets server port")
    parser.add_argument("-z", "--zoom", action="store", type=int, default=2, help="Scale factor")
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

    main(args.server, args.address, args.port, width=128, height=64, scale=args.zoom)
