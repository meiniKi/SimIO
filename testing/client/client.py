#!/usr/bin/env python3
#
# Copyright (c) 2024 Meinhard Kissich
# SPDX-License-Identifier: MIT
#
# File:     client.py
# Usage:    Simulated client for testing.
#

import socket

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 1080)
    client_socket.connect(server_address)
    print("Connected to server")

    try:
        while True:
            message = input("Enter a message to send (or 'quit' to exit): ")

            if message.lower() == 'quit':
                break
            
            client_socket.sendall(message.encode())
            print("Message sent to server")

            data = client_socket.recv(1024)
            print(">", data.decode())

    finally:
        client_socket.close()
        print("Connection closed")

if __name__ == "__main__":
    main()
