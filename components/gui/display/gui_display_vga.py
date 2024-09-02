#!/usr/bin/env python3
#
# Copyright (c) 2024 Meinhard Kissich
# SPDX-License-Identifier: MIT
#
# File:     gui_display_vga.py
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
from dataclasses import dataclass
from PIL import Image, ImageTk, ImageOps

logger = logging.getLogger(__name__)

@dataclass
class VGASetting:
    width:int = 800
    height:int = 600
    h_front_porch_px:int = 40
    h_sync_pulse_px:int = 128
    h_back_porch_px:int = 88
    v_front_porch_ln:int = 1
    v_sync_pulse_ln:int = 4
    v_back_porch_ln:int = 23
    low_active_hs_vs:bool = False
    color_depth:int=2


class DisplayState:
    def __init__(self, vga_settings:VGASetting, scale=1) -> None:
        self.h_front_porch_px = vga_settings.h_front_porch_px
        self.h_sync_pulse_px = vga_settings.h_sync_pulse_px
        self.h_back_porch_px = vga_settings.h_back_porch_px
        self.v_front_porch_ln = vga_settings.v_front_porch_ln
        self.v_sync_pulse_ln = vga_settings.v_sync_pulse_ln
        self.v_back_porch_ln = vga_settings.v_back_porch_ln

        self.w = vga_settings.width
        self.h = vga_settings.height
        self.scale = scale
        self.color_depth = vga_settings.color_depth

        # computed
        self.total_w_px = self.w + self.h_front_porch_px + self.h_sync_pulse_px + self.h_back_porch_px
        self.total_h_px = self.h + self.v_front_porch_ln + self.v_sync_pulse_ln + self.v_back_porch_ln

        # Store latest data
        self.framebuffer = np.zeros((self.h, self.w, 3), dtype=np.uint8)

        self.low_active_hs_vs = vga_settings.low_active_hs_vs

        self.hs_state = self.low_active_hs_vs
        self.hs_timestamp = 0

        self.vs_state = self.low_active_hs_vs
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
            self.process_hs_change(bool(frame_dict["value"]), frame_dict["timestamp"])
        elif frame_dict["type"] == "vs":
            self.process_vs_change(bool(frame_dict["value"]), frame_dict["timestamp"])
        elif frame_dict["type"] == "rgb":
            self.process_data_changed(self.adj_color(frame_dict["r"]), 
                                        self.adj_color(frame_dict["g"]), 
                                        self.adj_color(frame_dict["b"]), frame_dict["timestamp"])

    def process_data_changed(self, r, g, b, timestamp):
        logger.debug(f"[CHG] DATA -> ({r},{g},{b}) @ {timestamp}")
        self.update_framebuffer(self.rgb, timestamp)
        self.rgb = (r, g, b)
        

    def process_hs_change(self, hs, timestamp):
        logger.debug(f"[CHG] HS -> {hs} @ {timestamp}")
        self.update_framebuffer(self.rgb, timestamp)
        if (hs == self.low_active_hs_vs) and (self.hs_state != self.low_active_hs_vs):
            self.time_per_pixel = self.get_delta_t(timestamp, self.hs_timestamp) / self.h_sync_pulse_px
        self.hs_state = hs
        self.hs_timestamp = timestamp
        if hs == self.low_active_hs_vs:
            self.y += 1
        logger.debug(f"[UPDATE] y <- {self.y} => time per pixel: {self.time_per_pixel}")

    def process_vs_change(self, vs, timestamp):
        logger.debug(f"[CHG] VS -> {vs} @ {timestamp}")
        self.vs_state = vs
        self.vs_timestamp = timestamp
        # timestamp may be used to be more precise
        if vs == self.low_active_hs_vs:
            self.y = 0

    def adj_color(self, val):
        return val << (8-self.color_depth)

    def frmb_x(self, x):
        return x-self.h_back_porch_px
    
    def frmb_y(self, y):
        return y-self.v_back_porch_ln

    def update_framebuffer(self, rgb, timestamp):
        x_start = 0
        if self.get_delta_t(self.fb_update_timestamp, self.hs_timestamp) > 0:
            x_start = int(self.get_delta_t(self.fb_update_timestamp, self.hs_timestamp) // self.time_per_pixel)
        
        x_end = int(self.get_delta_t(timestamp, self.hs_timestamp) // self.time_per_pixel)
        logger.debug(f"update screen: {x_start} -> {x_end}")

        if (self.y >= self.v_back_porch_ln) and (self.y < self.v_back_porch_ln + self.h):
            for x in range(max(x_start, self.h_back_porch_px), min(x_end, self.h_back_porch_px+self.w)):
                logger.debug(f"({self.frmb_x(x), self.frmb_y(self.y)}) = {(rgb[0], rgb[1], rgb[2])}")
                self.framebuffer[self.frmb_y(self.y), self.frmb_x(x)] = (rgb[0], rgb[1], rgb[2])
        self.fb_update_timestamp = timestamp


    def get_image(self) -> ImageTk.Image:
        image=Image.fromarray(self.framebuffer)
        image = image.resize((self.w*self.scale,self.h*self.scale))
        return image

class VGADisplay(tk.Frame):
    SRV_PREFIX     = "[displayvga]-"

    def __init__(self, parent, vga_settings, scale=1, socks_connect=False, addr=None, port=1000, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.parent.title("VGA Screen")
        self.parent.geometry(f"{vga_settings.width*scale}x{vga_settings.height*scale}")
        self.parent.configure(bg="black")

        self.c = tk.Canvas(self.parent, width=vga_settings.width*scale, heigh=vga_settings.height*scale, bg="black")
        self.c.place(x=0, y=0)
        self.cimage = None

        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.rx_incomplete = ""
        self.rx_queue = queue.Queue()
        self.rx_thread = None
        self.stop_event = threading.Event()

        self.ds = DisplayState(vga_settings=vga_settings, scale=scale)

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
            #logger.debug(f"[srv -> display, frame] {frame}")
            self.handle_received(frame)
        # TODO: improve
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


def main(socks_connect, addr, port, vga_settings, scale):
    root = tk.Tk()
    VGADisplay(root, vga_settings=vga_settings, scale=scale,
               socks_connect=socks_connect, addr=addr, port=port).pack(side="top", fill="both", expand=True)
    root.mainloop()

def get_args():
    parser = argparse.ArgumentParser(description="DPI-C Verilog Model Gamepad")
    parser.add_argument("-s", "--server", action="store_true", help="Connect to sockets server")
    parser.add_argument("-a", "--address", action="store", type=str, default="localhost", help="Sockets server address")
    parser.add_argument("-p", "--port", action="store", type=int, default=1080, help="Sockets server port")
    parser.add_argument("-z", "--zoom", action="store", type=int, default=1, help="Scale factor")
    parser.add_argument("-d", "--depth", action="store", type=int, default=2, help="Color depth, i.e., number of bits per pixel")

    parser.add_argument("-x", "--width", action="store", type=int, default=800, help="VGA screen width")
    parser.add_argument("-y", "--height", action="store", type=int, default=600, help="VGA screen height")
    parser.add_argument("-l", "--low-active", action="store_true", help="Make HS VS low active")
    parser.add_argument("--h-front-porch", action="store", type=int, default=40, help="VGA horizontal front porch pixel")
    parser.add_argument("--h-sync-pulse", action="store", type=int, default=128, help="VGA horizontal sync pulse pixel")
    parser.add_argument("--h-back-porch", action="store", type=int, default=88, help="VGA horizontal back porch pixel")
    parser.add_argument("--v-front-porch", action="store", type=int, default=1, help="VGA vertical front porch lines")
    parser.add_argument("--v-sync-pulse", action="store", type=int, default=4, help="VGA vertical sync pulse lines")
    parser.add_argument("--v-back-porch", action="store", type=int, default=23, help="VGA vertical back porch lines")

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

    vga_settings = VGASetting(width=args.width, 
                                height=args.height,
                                h_front_porch_px=args.h_front_porch,
                                h_sync_pulse_px=args.h_sync_pulse,
                                h_back_porch_px=args.h_back_porch,
                                v_front_porch_ln=args.v_front_porch,
                                v_sync_pulse_ln=args.v_sync_pulse,
                                v_back_porch_ln=args.v_back_porch,
                                low_active_hs_vs=args.low_active,
                                color_depth=args.depth)

    main(args.server, args.address, args.port, vga_settings, scale=args.zoom)
