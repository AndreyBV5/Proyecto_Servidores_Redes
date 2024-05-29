# ServidorVideos.py
import os
import socket
import json
import time
import argparse

def get_video_list(video_dir):
    videos = os.listdir(video_dir)
    return videos

def main():
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description='Servidor de Videos')
    parser.add_argument('port', type=int, help='Puerto en que escucha el servidor')
    parser.add_argument('video_dir', type=str, help='Ruta de la carpeta en que se almacenan los vídeos')

    # Parsear los argumentos
    args = parser.parse_args()
    port = args.port
    video_dir = args.video_dir

    host = 'localhost'

    print(f"Servidor de videos iniciado en {host}:{port}")
    print(f"Almacenando videos desde {video_dir}")

    s = socket.socket()
    s.bind((host, port))

    # Conectar al servidor principal y envíar la lista de videos
    main_server_host = 'localhost'
    main_server_port = 5000
    main_server_socket = socket.socket()
    while True:
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

if _name_ == '_main_':
    main()