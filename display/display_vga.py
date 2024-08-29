#!/usr/bin/env python3
#
# Copyright (c) 2024 Meinhard Kissich
# SPDX-License-Identifier: MIT
#
# File:     display_vga.py
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
    def __init__(self, w=800, h=640, scale=2, color_depth=2) -> None:
        self.h_front_porch_px = 40
        self.h_sync_pulse_px = 128
        self.h_back_porch_px = 88
        self.v_front_porch_ln = 1
        self.v_sync_pulse_ln = 4
        self.v_back_porch_ln = 23

        self.w = w
        self.h = h
        self.scale = scale
        self.color_depth = color_depth

        # computed
        self.total_h_px = self.h + self.v_front_porch_ln + self.v_sync_pulse_ln + self.v_back_porch_ln
        self.total_w_px = self.w + self.h_front_porch_px + self.h_sync_pulse_px + self.h_back_porch_px

        # Store latest data
        self.framebuffer = np.zeros((h, w, 3), dtype=np.uint8)

        self.hs_state = 0
        self.hs_timestamp = 0

        self.vs_state = 0
        self.vs_timestamp = 0

        self.rgb = (0,0,0)
        self.fb_update_timestamp = 0

        self.y = 0

        self.time_per_pixel = 1.0

    def get_delta_t(self, t_new, t_old):
        return (t_new - t_old) if (t_new > t_old) else (2**32 - t_old + t_new)

    def handle_rx(self, json_data):
        frame_dict = json.loads(json_data)
        if not "type" in frame_dict:
            logger.warning("Received invalid json: key 'type' does not exist")
        if frame_dict["type"] == "hs":
            self.process_hs_change(frame_dict["value"], frame_dict["timestamp"])
        elif frame_dict["type"] == "vs":
            self.process_vs_change(frame_dict["value"], frame_dict["timestamp"])
        elif frame_dict["type"] == "rgb":
            self.process_data_changed(frame_dict["r"], frame_dict["g"], frame_dict["b"], frame_dict["timestamp"])


    def process_data_changed(self, r, g, b, timestamp):
        self.rgb = (r, g, b)
        self.update_framebuffer(self.rgb, timestamp)
        

    def process_hs_change(self, hs, timestamp):
        self.update_framebuffer(self.rgb, timestamp)
        if (hs == 0) and (self.hs_state == 1):
            self.time_per_pixel = self.get_delta_t(timestamp, self.hs_timestamp) / self.h_sync_pulse_px
        self.hs_state = hs
        self.hs_timestamp = timestamp
        if hs == 0:
            self.y += 1

    def process_vs_change(self, vs, timestamp):
        self.vs_state = vs
        self.vs_timestamp = timestamp
        # timestamp may be used to be more precise
        if vs == 0:
            self.y = 0

    def adj(self, val):
        return val << (8-self.color_depth)

    def update_framebuffer(self, rgb, timestamp):
        x_start = 0
        if self.get_delta_t(self.fb_update_timestamp, self.hs_timestamp) > 0:
            x_start = int(self.get_delta_t(self.fb_update_timestamp, self.hs_timestamp) // self.time_per_pixel)
        
        x_end = int(self.get_delta_t(timestamp, self.hs_timestamp) // self.time_per_pixel)

        if (self.y >= self.v_front_porch_ln) and (self.y < self.v_front_porch_ln + self.h):
            for x in range(max(x_start, self.h_front_porch_px), min(x_end, self.h_front_porch_px+self.w)):
                self.framebuffer[self.y-self.v_front_porch_ln, x-self.h_front_porch_px] = (self.adj(rgb[0]), self.adj(rgb[1]), self.adj(rgb[2]))
        self.fb_update_timestamp = timestamp


    def get_image(self) -> ImageTk.Image:
        image=Image.fromarray(self.framebuffer)
        image = image.resize((self.w*self.scale,self.h*self.scale))
        return image

class VGADisplay(tk.Frame):
    SRV_PREFIX     = "[displayvga]-"

    def __init__(self, parent, w=800, h=640, color_depth=2, scale=2, socks_connect=False, addr=None, port=1000, *args, **kwargs):
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

        self.ds = DisplayState(w, h, color_depth, scale)

        self.main_frame = tk.Frame(self)
        self.main_frame.pack()

        self.UPDATE_X_FRAMES = 300
        self.update_x_frames_cnt = 0

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
            data = socket.recv(256*1024).decode('utf-8')
            queue.put(data)

    def recv_state(self):
        if not self.rx_queue.empty():
            self.rx_incomplete += self.rx_queue.get()
        
        while "\n" in self.rx_incomplete:
            tmp = self.rx_incomplete.split('\n', 1)
            frame = tmp[0]
            self.rx_incomplete = tmp[1]
            logger.info(f"[srv -> display, frame] {frame}")
            self.handle_received(frame)
        self.after(1, self.recv_state)

    def handle_received(self, frame):
        if not frame.startswith(VGADisplay.SRV_PREFIX):
            return
        frame = frame.removeprefix(VGADisplay.SRV_PREFIX)
        self.ds.handle_rx(frame)
        self.update_x_frames_cnt += 1
        if self.update_x_frames_cnt >= self.UPDATE_X_FRAMES:
            self.update_x_frames_cnt = 0
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


def main(socks_connect, addr, port, width, height, scale, color_depth):
    root = tk.Tk()
    VGADisplay(root, width, height, scale, color_depth, socks_connect, addr, port).pack(side="top", fill="both", expand=True)
    root.mainloop()

def get_args():
    parser = argparse.ArgumentParser(description="DPI-C Verilog Model Gamepad")
    parser.add_argument("-s", "--server", action="store_true", help="Connect to sockets server")
    parser.add_argument("-a", "--address", action="store", type=str, default="localhost", help="Sockets server address")
    parser.add_argument("-p", "--port", action="store", type=int, default=1080, help="Sockets server port")
    parser.add_argument("-z", "--zoom", action="store", type=int, default=1, help="Scale factor")
    parser.add_argument("-d", "--depth", action="store", type=int, default=2, help="Color depth, i.e., number of bits per pixel")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )

    main(args.server, args.address, args.port, width=800, height=640, scale=args.zoom, color_depth=args.depth)
