# Servidor de Videos
import os
import socket
import json
import time  # Importa el módulo time para usar la función sleep

def get_video_list(video_dir):
    videos = os.listdir(video_dir)
    return videos

def main():
    host = 'localhost'
    port = 5001  # Configura el puerto directamente en el código
    video_dir = r'C:\Users\andre\Videos\ingenieria'  # Configura la ruta de la carpeta de videos directamente en el código

    print(f"Servidor de videos iniciado en {host}:{port}")
    print(f"Almacenando videos desde {video_dir}")

    s = socket.socket()
    s.bind((host, port))

    # Conéctate al servidor principal y envía la lista de videos
    main_server_host = 'localhost'
    main_server_port = 5000
    main_server_socket = socket.socket()
    while True:  # Añade este bucle para intentar conectarse al servidor principal hasta que tenga éxito
        try:
            main_server_socket.connect((main_server_host, main_server_port))
            break
        except ConnectionRefusedError:
            print("Conexión rechazada, intentando de nuevo en 5 segundos...")
            time.sleep(5)  # Espera 5 segundos antes de intentar de nuevo
    videos = get_video_list(video_dir)
    main_server_socket.send(json.dumps(videos).encode('utf-8'))
    main_server_socket.close()

    s.listen(1)
    while True:
        c, addr = s.accept()
        print("Connection from: " + str(addr))
        while True:
            data = c.recv(1024).decode('utf-8')
            if not data:
                break
            print("from connected user: " + data)
            if data == 'get_video_list':
                videos = get_video_list(video_dir)
                c.send(json.dumps(videos).encode('utf-8'))
        c.close()

if __name__ == '__main__':
    main()
