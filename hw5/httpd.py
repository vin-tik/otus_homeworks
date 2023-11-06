#!/usr/bin/env python
# coding: utf-8

import argparse
import logging
import os
import socket
from concurrent.futures import ThreadPoolExecutor
import urllib


DOCUMENT_ROOT = './'
accepted_methods = ['GET', 'HEAD']

response_status = {'OK': 200,
                   'FORBIDDEN': 403,
                   'NOT_FOUND': 404,
                   'METHOD_NOT_ALLOWED': 405}

def get_args():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--host', default='localhost')
    args_parser.add_argument('-p', '--port', default=8080, type=int)
    args_parser.add_argument('-w', '--workers', default=1, type=int, help="Count workers")
    args_parser.add_argument('-r', '--document-root', default=DOCUMENT_ROOT, help='Document root folder')
    return args_parser.parse_args()

class BaseServer:
    def __init__(self, host, port, max_workers, document_root):
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.document_root = document_root
        self.socket_timeout = 10

    def serve_forever(self):
        serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            serv_socket.bind(
                             (
                                 self.host, self.port
                              )
                             )
            serv_socket.listen(self.max_workers)
            executor = ThreadPoolExecutor(max_workers=self.max_workers)
            while True:
                client_socket, _ = serv_socket.accept()
                client_socket.settimeout(self.socket_timeout)
                executor.submit(ConnectHandler, client_socket, self.document_root)
        except socket.error as e:
            raise ConnectionError

class ConnectHandler:
    def __init__(self, c_socket, document_root):
        self.c_socket = c_socket
        self.document_root = document_root
        self.method, self.url, self.http_ver = self.parse_request()
        
        self.response_status = None
        self.response_data = None
        self.response_header = {}
        self.method_handler()

    def parse_request(self, c_socket):
        maxline = 64*1024
        rfile = c_socket.makefile('rb')
        raw = rfile.readline(maxline + 1)
        if len(raw) > maxline:
            raise Exception('Request line is too long')

        req_line = str(raw, 'iso-8859-1')
        req_line = req_line.rstrip('\r\n')
        req_parts = req_line.split()
        if len(req_parts) != 3:
            raise Exception('Malformed request line')

        method, url, httpv = req_parts
        if httpv != 'HTTP/1.1':
            raise Exception('Unexpected HTTP version')

        url = urllib.parse.unquote(url, encoding='utf-8', errors='replace')
        url = urllib.parse.urlparse(url).path
        return method, url, httpv
    
    def method_handler(self):
        is_send_data = True
        if self.method in accepted_methods:
            self.request_method()
            if self.method == 'HEAD':
                is_send_data = False
        else:
            self.response_status = response_status['METHOD_NOT_ALLOWED']

        response = self.create_response(is_send_data)
        self.send_response(response)

    def request_method(self):
        path = os.path.abspath(self.document_root + self.url)
        if os.path.exists(path) and '../' not in self.url:
            if os.path.isfile(path) and not self.url.endswith('/'):
                with open(path, 'rb') as data:
                    self.response_data = data.read()
                    self.response_status = response_status['OK']
                    self.response_header['Content-Type'] = self.define_content_type(path)

            elif self.check_index_file(path):
                self.response_status = response_status['OK']
                self.response_header['Content-Type'] = 'text/html'
                self.response_data = b'<html>Directory index file</html>\n'

            elif os.path.isfile(path) and self.url.endswith('/'):
                self.response_status = response_status['NOT_FOUND']

            else:
                self.response_status = response_status['NOT_FOUND']
        else:
            self.response_status = response_status['NOT_FOUND']
      
    def define_content_type(self, filepath):
        default_extentions = {'.html': 'html',
                              '.css': 'css',
                              '.js': 'js',
                              '.jpg': 'jpg',
                              '.jpeg': 'jpeg',
                              '.png': 'png',
                              '.gif': 'gif',
                              '.swf': 'swf'}
        ext = os.path.splitext(filepath)
        return default_extentions.get(ext)
            
    def check_index_file(self, path):
            if os.path.isdir(path):
                list_files = os.listdir(path)
                return 'index.html' in list_files
            else:
                return False

    def create_header(self):
        headers = ''
        if self.response_data:
            self.response_header['Content-Length'] = len(self.response_data)

        for key, value in self.response_header.items():
            headers += f'{key}: {value}\r\n'
        return headers.encode()

    def create_response(self, is_send_data=True):
        status_line = f'HTTP/1.1 {self.response_status}'.encode()
        headers = self.create_header()
        response = status_line + b'\r\n' + headers + b'\r\n'

        if self.response_data and is_send_data:
            response += self.response_data + b'\r\n'
        return response
    
    def send_response(self, response):
        self.c_socket.sendall(response)
        self.c_socket.close()  

if __name__ == "__main__":
    args = get_args()

    logging.basicConfig(level=logging.INFO,
                        datefmt='%Y.%m.%d %H:%M:%S',
                        format='[%(asctime)s] %(threadName)s %(levelname)s %(message)s',
                        )

    server = BaseServer(host=args.host,
                    port=args.port,
                    max_workers=args.workers,
                    document_root=args.document_root,
                    )

    server.serve_forever()
