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
import socks

KEY_DEFAULT_COLOR = "lightgray"

def setup_windows(w=128, h=64, scale=2):

    root = tk.Tk()
    root.title("Display")
    root.geometry(f"{w*scale}x{h*scale}")
    root.configure(bg="black")

    c = tk.Canvas(root, width=w*scale, heigh=h*scale, bg="black")
    c.place(x=0, y=0)

    return root



def main(socks_connect=True, addr=None, port=1000):
    if socks_connect:
        socks.set_default_proxy(socks.SOCKS5, addr, port)
        socket.socket = socks.socksocket

    root = setup_windows()
    root.mainloop()


if __name__ == "__main__":
    main(socks_connect=False)