#!/usr/bin/env python3

import io
import os
import pickle
import socket
import subprocess
import struct
import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

try:
    import yaml
    import pydirectinput
    import pyautogui

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
except ImportError:
    pass

# A way to dynamically reload the app.
# My current solution is my having a button after you edit the config
# This should also notify the app so that it will refresh

# Rewrite this code using kivy, tkinter is only use for testing purpose, you would use pydroid3 on android to use this on android device

# Code is very messy, I failed to close some window element due to unable to close window from thread and can't have 2 tk.Tk()
# Likely fixed once I use kivy to overhaul the UI, but we'll see
class Server():
    """
    The server that will receives input from client.
    """
    def __init__(self) -> None:
        self.server = None
        self.connection = None
        self.client_address = None

    def start_server(self):
        host = socket.gethostname()
        port = 8000

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))

        print("Listening on: " + str(socket.gethostbyname(host)) + ':' + str(port))

        # blocking, I literally in a fucking loop because I can't figure how to close server because this bitch kept raising about errors
        self.server.listen(1)
        self.connection, self.client_address = self.server.accept()
        print(str(self.client_address))

        return True

    # def force_close(self):
    #     c = socket.socket()
    #     c.connect((socket.gethostbyname, 8000))

    def close_server(self):
        if self.server:
            self.server.shutdown(socket.SHUT_RDWR)
            self.connection = None
        else:
            print("There is no server running")
    
    def close_client(self):
        if self.connection:
            self.connection.close()
            self.connection = None
        else:
            print("There is no client connected")
    
    def receive_data(self):
        if not self.connection:
            print("There is no client to listen to")
            return

        data = self.connection.recv(4)
        data_size = struct.unpack('>I', data)[0]
        data_struct = b''
        leftover = data_size
        while leftover != 0:
            data_struct += self.connection.recv(leftover)
            leftover = data_size - len(data_struct)

        return data_struct
    
    def send_data(self, data: str = ''):
        if not self.connection:
            print("There is no client to send to")
        
        self.connection.sendall(struct.pack('>I', len(data)))
        self.connection.sendall(data)


class Client():
    """
    The client that is trying to connect through server from another device.
    """
    def __init__(self) -> None:
        self.client = None

    def connect(self, address: str, port: int):
        """
        Connect to a server through an address.
        
        The server should be on the same connection as yours, either through same wifi connection or hotspot from other device.
        """
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((address, int(port)))
            print("Connected to: " + str(address) + ':' + str(port))
            return True
        except OSError as e:
            print(e)
            self.client = None
            return e
    

    def send_data(self, data: str = ''):
        if not self.client:
            print("There is no server to send to")
        
        self.client.sendall(struct.pack('>I', len(data)))
        self.client.sendall(data)

    def receive_data(self):
        if not self.client:
            print("There is no server to listen to")
            return

        data = self.client.recv(4)
        data_size = struct.unpack('>I', data)[0]
        data_struct = b''
        leftover = data_size
        while leftover != 0:
            data_struct += self.client.recv(leftover)
            leftover = data_size - len(data_struct)

        return data_struct

    def close_client(self):
        if self.client:
            self.client.close()
            self.client = None
        else:
            print("You aren't connected to any server")

window = None
mainframe = None
server = None
client = None
pop_up = None
address_entry = None
index = 0

def image_process(config):
    sizes = []

    for x in config.keys():
        size = config[x]['size']
        if size in sizes:
            continue

        sizes.append(size)

    file_objects = {}
    for x in os.walk('img'):
        for y in sizes:
            di = {}
            for z in x[2]:
                d = {}
                fn, fm = z.rsplit('.', 1)
                if fm.lower() == 'jpg':
                    fm = 'jpeg'
                if z in ('left_arrow.png', 'right_arrow.png'):
                    img = Image.open(f'img/{z}')
                    img = img.resize((75, 75), Image.ANTIALIAS)
                    f = io.BytesIO()
                    img.save(f, format = fm)
                    f.seek(0)
                    f = f.getvalue()
                    d[fn] = f
                    di = {**di, **d}
                else:
                    img = Image.open(f'img/{z}')
                    img = img.resize((y, y), Image.ANTIALIAS)
                    f = io.BytesIO()
                    img.save(f, format = fm)
                    f.seek(0)
                    f = f.getvalue()
                    d[fn] = f
                    di = {**di, **d}
            file_objects[y] = di
    return file_objects


def window_init():
    global window
    global mainframe

    window = tk.Tk()
    s = ttk.Style(window)

    s.configure('TFrame', background = '#0D1117')
    s.configure('TLabel', background = '#0D1117', foreground = '#E5E5E5')
    s.configure('TRadiobutton', background = '#0D1117', foreground = '#E5E5E5')
    s.configure('TEntry', background = '#0D1117', foreground = 'black')
    s.configure('TButton', background = '#0D1117')

    window.title('Shurtcut deck - Configure')
    window.tk.call('tk', 'scaling', 2.0)
    tk.Grid.columnconfigure(window, 0, weight = 1)
    tk.Grid.rowconfigure(window, 0, weight = 1)

    mainframe = ttk.Frame(window)
    mainframe.grid(column = 0, row = 0, sticky = tk.N+tk.W+tk.E+tk.S)

    for row_index in range(10):
        tk.Grid.rowconfigure(mainframe, row_index, weight = 1)
        for col_index in range(2):
            tk.Grid.columnconfigure(mainframe, col_index, weight = 1)

    ttk.Label(mainframe, text = 'Choose network:').grid(row = 1, column = 2, sticky = tk.N)

    receiver_button = ttk.Button(mainframe, text = 'Receive', command = lambda:host())
    receiver_button.grid(row = 2, column = 1, sticky = tk.W)

    sender_button = ttk.Button(mainframe, text = 'Send', command = lambda:guest())
    sender_button.grid(row = 2, column = 3, sticky = tk.E)

    ttk.Label(mainframe, text = '').grid(row = 13, column = 2)

    ttk.Label(mainframe, text = 'version: 0.0.1', foreground = '#00FF00').grid(row = 14, column = 1, sticky=tk.W+tk.S)

    for x in mainframe.winfo_children(): 
        x.grid_configure(padx=5, pady=5)

    window.mainloop()

def window_receiver():
    def loop():
        while True:
            res = server.receive_res = server.receive_data()
            res = pickle.loads(res)

            if list(res.keys())[0] == 'key':
                key = res['key']
                type = res['type']
                scheduled_keys = []
                coordinate = None
                for x in key:
                    x = str(x)
                    if x.startswith('click'):  
                        try:
                            _ = x.split(' ')
                            coordinate = _[1].split('x')
                            coordinate[1]
                        except IndexError:
                            coordinate = ()
                    else:
                        scheduled_keys.append(x)

                if scheduled_keys:
                    if type == 'pyautogui':
                        if coordinate is None:
                            if len(scheduled_keys) != 1:
                                pyautogui.hotkey(*scheduled_keys)
                            else:
                                pyautogui.press(scheduled_keys, interval = 0.1)
                        else:
                            with pyautogui.hold(scheduled_keys):
                                if isinstance(coordinate, tuple):
                                    pyautogui.click()
                                else:
                                    pyautogui.click(*coordinate)
                    else:
                        if coordinate is None:
                            pydirectinput.press(scheduled_keys, interval = 0.1)
                        else:
                            for x in scheduled_keys:
                                pydirectinput.keyDown(x)
                            if isinstance(coordinate, tuple):
                                pydirectinput.click()
                            else:
                                pydirectinput.click(*coordinate)
                            for x in scheduled_keys:
                                pydirectinput.keyUp(x)
                                
                elif not coordinate is None and not scheduled_keys:
                    if isinstance(coordinate, tuple):
                        if type == 'pyautogui':
                            pyautogui.click()
                        else:
                            pydirectinput.click()
                    else:
                        if type == 'pyautogui':
                            pyautogui.click(*coordinate)
                        else:
                            pydirectinput.click(*coordinate)

            elif list(res.keys())[0] == 'script':
                args = res['script']
                subprocess.Popen(args.split())

    def reload():
        global server
        global config

        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)

        img = image_process(config)
        reload_data = {'reload': config, 'images': img}
        server.send_data(pickle.dumps(reload_data))

    def create_window():
        global window
        global mainframe
        
        window = tk.Tk()
        s = ttk.Style(window)

        s.configure('TFrame', background = '#0D1117')
        s.configure('TLabel', background = '#0D1117', foreground = '#E5E5E5')
        s.configure('TRadiobutton', background = '#0D1117', foreground = '#E5E5E5')
        s.configure('TEntry', background = '#0D1117', foreground = 'black')
        s.configure('TButton', background = '#0D1117')

        window.title('Shurtcut deck - Host')
        window.tk.call('tk', 'scaling', 2.0)
        tk.Grid.columnconfigure(window, 0, weight = 1)
        tk.Grid.rowconfigure(window, 0, weight = 1)

        mainframe = ttk.Frame(window)
        mainframe.grid(column = 0, row = 0, sticky = tk.N+tk.W+tk.E+tk.S)

        for row_index in range(10):
            tk.Grid.rowconfigure(mainframe, row_index, weight = 1)
            for col_index in range(2):
                tk.Grid.columnconfigure(mainframe, col_index, weight = 1)

        ttk.Label(mainframe, text = 'You are currently receiving inputs from: ' + str(server.client_address)).grid(row = 1, column = 1, sticky = tk.N)

        receiver_button = ttk.Button(mainframe, text = 'Reload', command = lambda:reload())
        receiver_button.grid(row = 2, column = 1, sticky = tk.W)

        ttk.Label(mainframe, text = '').grid(row = 13, column = 2)

        ttk.Label(mainframe, text = 'version: 0.0.1', foreground = '#00FF00').grid(row = 14, column = 1, sticky=tk.W+tk.S)

        for x in mainframe.winfo_children(): 
            x.grid_configure(padx=5, pady=5)

        window.mainloop()

    global server
    global window
    global config
    img = image_process(config)
    data = {'init': config, 'images': img}
    server.send_data(pickle.dumps(data))
    t1 = threading.Thread(target = lambda: loop(), name='Main window server loop thread')
    t1.start()
    create_window()

m = None
def window_sender():
    def loop():
        while True:
            res = client.receive_data()
            res = pickle.loads(res)

            if list(res.keys())[0] == 'reload':
                global m
                global index
                m.after(1, lambda: m.destroy())
                index = 0
                preset_build(res['reload'], res['images'])

    def preset_build(config: dict, images: dict):
        def before():
            global index
            global m
            m.destroy()
            index -= 1
            preset_build(config, images)

        def after():
            global index
            global m
            m.destroy()
            index += 1
            preset_build(config, images)
        
        def button_command(index_command: int):
            global client
            inputs = list(config[index_name]['icons'][index_command].values())[0]
            if isinstance(inputs, list):
                data = {'key': inputs, 'type': config[index_name]['input']}
                client.send_data(pickle.dumps(data))
            else:
                data = {'script': inputs}
                client.send_data(pickle.dumps(data))

        global window
        global index
        global m
        max_index = len(config.keys()) - 1

        index_name = list(config)[index]
        gridx = config[index_name]['gridx']
        gridy = config[index_name]['gridy']

        # It include file format because I'm planning to add animated image soon
        filename_keys = [x for x in images[list(images.keys())[0]].keys()]
        assets = []
        for _ in filename_keys:
            assets.append(_.rsplit('.', 1))

        icons = config[index_name]['icons']
        w_h = config[index_name]['size']

        m = tk.Toplevel(window)
        s = ttk.Style(m)

        s.configure('TFrame', background = '#0D1117')
        s.configure('TLabel', background = '#0D1117', foreground = '#E5E5E5')
        s.configure('TRadiobutton', background = '#0D1117', foreground = '#E5E5E5')
        s.configure('TEntry', background = '#0D1117', foreground = 'black')
        s.configure('TButton', background = '#0D1117')

        m.title('Shurtcut deck')
        m.tk.call('tk', 'scaling', 3.0)
        tk.Grid.columnconfigure(m, 0, weight = 1)
        tk.Grid.rowconfigure(m, 0, weight = 1)

        mainframe = ttk.Frame(m)
        mainframe.grid(column = 0, row = 0, sticky = tk.N+tk.W+tk.E+tk.S)

        # for row_index in range(10):
        #     tk.Grid.rowconfigure(mainframe, row_index, weight = 1)
        #     for col_index in range(2):
        #         tk.Grid.columnconfigure(mainframe, col_index, weight = 1)

        if not index == 0:
            back = images[w_h]['left_arrow']
            back = ImageTk.PhotoImage(Image.open(io.BytesIO(back)))
            _ = ttk.Button(mainframe, image = back, command = lambda:before())
            _.grid(row = 1, column = 1)
            _.image = back
        if not index == max_index:
            next = images[w_h]['right_arrow']
            next = ImageTk.PhotoImage(Image.open(io.BytesIO(next)))
            _ = ttk.Button(mainframe, image = next, command = lambda:after())
            _.grid(row = 1, column = 6)
            _.image = next

        null_image = images[w_h]['null']
        null_image = ImageTk.PhotoImage(Image.open(io.BytesIO(null_image)))

        index_count = 0
        for y in range(gridy):
            y += 3
            for x in range(gridx):
                x += 1
                item = icons[index_count]
                index_count += 1

                if isinstance(item, dict):
                    filename = list(item.keys())[0]

                    img = images[w_h][filename]
                    img = ImageTk.PhotoImage(Image.open(io.BytesIO(img)))
                    _ = ttk.Button(mainframe, image = img, command = lambda index_count=index_count: button_command(index_count-1))
                    _.grid(row = y, column = x)
                    _.image = img

                else:
                    _ = ttk.Button(mainframe, image = null_image)
                    _.grid(row = y, column = x)
                    _.image = null_image

        ttk.Label(mainframe, text = index_name, font = ('TkDefaultFont', 25)).grid(row = 1, column = 2, columnspan = 3)

        for w in mainframe.winfo_children(): 
            w.grid_configure(padx=15, pady=15)

        m.mainloop()

    global client

    data = client.receive_data()
    data = pickle.loads(data)
    config = data['init']
    t2 = threading.Thread(target = lambda: loop(), name='Main window client loop thread')
    t2.start()
    preset_build(config, data['images'])

def ping():
    global address_entry
    global client

    link = address_entry.get()
    link = link.strip('http://')

    if not ':' in link:
        return "Address doesn't include port"

    link = link.split(':')

    s = client.connect(*link)

    if not s is True:
        return s
    
    return True

def input_confirm():
    global pop_up
    global window
    res = ping()

    if not res is True:
        pop_up = tk.Toplevel(window)
        pop_up.title('Failed')
        pop_up.tk.call('tk', 'scaling', 5.0)

        m = ttk.Frame(pop_up)
        m.grid(column = 0, row = 0, sticky = tk.N+tk.W+tk.E+tk.S)

        # ttk.Label(m, text = 'The server did not respond, this is likely because:\n- You input wrong address\n- Firewall is blocking either connection\n- Either your device doesn\'t connect to the same connection').grid(row = 1, column = 2)
        ttk.Label(m, text = str(res)).grid(row = 1, column = 2)
        ttk.Label(m, text='').grid(row = 2, column = 3)
        tk.Button(m, text = "close", command = lambda:pop_up.destroy()).grid(row = 3, column = 2)

        for x in m.winfo_children():
            x.grid_configure(padx = 5, pady = 5)
    else:
        pop_up.destroy()
        window.withdraw()
        pop_up = None
        window = None
        window_sender()

def host():
    # def w_destroy():
    #     global pop_up
    #     global server
    #     server.close_server()
    #     pop_up.destroy()
    #     pop_up = None

    def w_destroy():
        global pop_up
        global window
        global server
        t4.join()
        pop_up.after(1, lambda: pop_up.destroy())
        window.withdraw()
        pop_up = None
        window = None
        window_receiver()

    global server
    global pop_up

    for x in mainframe.winfo_children():
        try:
            x.config(state = tk.DISABLED)
        except:
            print('Unable to change to disabled state for: ' + x.winfo_class())

    server = Server()
    t4 = threading.Thread(target = lambda:server.start_server(), name = 'server')
    t5 = threading.Thread(target = lambda:w_destroy(), name = 'placeholder')
    t4.start()
    t5.start()

    address = socket.gethostbyname(socket.gethostname())

    pop_up = tk.Toplevel(window)
    pop_up.title('')
    pop_up.tk.call('tk', 'scaling', 2.0)
    pop_up.protocol("WM_DELETE_WINDOW", True)

    m = ttk.Frame(pop_up)
    m.grid(column = 0, row = 0, sticky = tk.N+tk.W+tk.E+tk.S)

    ttk.Label(m, text = 'On your device, input the ip shown here to connect').grid(row = 1, column = 2)
    ttk.Label(m, text = address + ':8000').grid(row = 2, column = 2)
    ttk.Label(m, text='').grid(row = 3, column = 2)
    # ttk.Entry(m, textvariable = link).grid(row = 4, column = 1, columnspan = 3)
    # tk.Button(m, text = "continue", command = lambda:input_confirm()).grid(row = 4, column = 1)
    # tk.Button(m, text = "cancel", command = lambda:w_destroy()).grid(row = 4, column = 3)

    for x in m.winfo_children():
        x.grid_configure(padx = 5, pady = 5)

def guest():
    def w_destroy():
        global pop_up
        global client
        client.close_client()
        pop_up.destroy()
        pop_up = None

    global client
    global pop_up
    global address_entry

    for x in mainframe.winfo_children():
        try:
            x.config(state = tk.DISABLED)
        except:
            print('Unable to change to disabled state for: ' + x.winfo_class())

    client = Client()

    address_entry = tk.StringVar(value = '')

    pop_up = tk.Toplevel(window)
    pop_up.title('')
    pop_up.tk.call('tk', 'scaling', 5.0)
    pop_up.protocol("WM_DELETE_WINDOW", True)

    m = ttk.Frame(pop_up)
    m.grid(column = 0, row = 0, sticky = tk.N+tk.W+tk.E+tk.S)

    ttk.Label(m, text = 'On your device, input the IP shown into here').grid(row = 1, column = 2)
    ttk.Label(m, text='').grid(row = 2, column = 2)
    ttk.Entry(m, textvariable = address_entry).grid(row = 3, column = 1, columnspan = 3)
    tk.Button(m, text = "continue", command = lambda:input_confirm()).grid(row = 4, column = 1)
    tk.Button(m, text = "cancel", command = lambda:w_destroy()).grid(row = 4, column = 3)

    for x in m.winfo_children():
        x.grid_configure(padx = 5, pady = 5)

# placeholder UI, I don't know how to dynamically change the entire UI, though change only single element works
if __name__ == "__main__":
    window_init()