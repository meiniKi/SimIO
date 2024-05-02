#!/usr/bin/env python3
#
# Copyright (c) 2024 Meinhard Kissich
# SPDX-License-Identifier: MIT
#
# File:     server.py
# Usage:    Sockets server to exchange data between models and
#           SystemVerilog simulation.
#

import socket
import argparse
import logging
import threading

logger = logging.getLogger(__name__)

class Server:
    def __init__(self, addr, port, nmax) -> None:
        self.clients = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info(f"Starting server {addr}:{port} ...")
        self.sock.bind((addr, port))
        self.sock.listen(nmax)

    def run(self):
        try:
            while True:
                client_socket, client_addr = self.sock.accept()
                self.clients.append(client_socket)

                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr, self.clients))
                client_thread.start()
        except KeyboardInterrupt:
            logger.info("Shutting down server")
            self.sock.close()

    def handle_client(self, client_socket, client_addr, clients):
        logger.info(f"New client: {client_addr}")
        while True:
            try:
                data = client_socket.recv(128)
                if not data:
                    break
                logger.info(f"[{client_addr} -> srv]: {data}")

                # Broadcast
                for c in clients:
                    if c != client_socket:
                        logger.info(f"[srv -> {c.getpeername()}]: {data}")
                        c.sendall(data)

            except Exception as e:
                logger.error(e)
                break

        clients.remove(client_socket)
        client_socket.close()
        logger.info(f"{client_addr} closed")


def main(addr, port, nmax):
    s = Server(addr, port, nmax)
    s.run()

def get_args():
    parser = argparse.ArgumentParser(description="Socks server for Verilog DPI-C data exchange")
    parser.add_argument("-a", "--address", action="store", type=str, default="localhost", help="Sockets server address")
    parser.add_argument("-p", "--port", action="store", type=int, default=1080, help="Sockets server port")
    parser.add_argument("-n", "--nmax", action="store", type=int, default=5, help="Maximum number of connections")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )

    args = get_args()
    main(addr=args.address, port=args.port, nmax=args.nmax)



