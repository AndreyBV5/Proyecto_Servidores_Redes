import os
import socket
import json
import time
import argparse

def get_video_list(video_dir):
    videos = os.listdir(video_dir)
    return videos

def main():
    parser = argparse.ArgumentParser(description='Servidor de Videos')
    parser.add_argument('port', type=int, help='Puerto en que escucha el servidor')
    parser.add_argument('video_dir', type=str, help='Ruta de la carpeta en que se almacenan los vídeos')

    args = parser.parse_args()
    port = args.port
    video_dir = args.video_dir

    host = 'localhost'  # IP del Servidor de Videos

    print(f"Servidor de videos iniciado en {host}:{port}")
    print(f"Almacenando videos desde {video_dir}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))

    # Conectar al Servidor Principal y enviar la lista de videos
    main_server_host = '192.168.0.9'  # IP del Servidor Principal
    main_server_port = 5000           # Puerto del Servidor Principal
    main_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            main_server_socket.connect((main_server_host, main_server_port))
            break
        except ConnectionRefusedError:
            print("Conexión rechazada, intentando de nuevo en 5 segundos...")
            time.sleep(5)  # Espera 5 segundos antes de intentar de nuevo

    video_server_info = {
        'host': host,
        'port': port,
        'videos': get_video_list(video_dir)
    }
    main_server_socket.send(json.dumps(video_server_info).encode('utf-8'))
    main_server_socket.close()

    s.listen(5)  # Permitir múltiples conexiones
    while True:
        c, addr = s.accept()
        print("Conexión desde: " + str(addr))
        while True:
            data = c.recv(1024).decode('utf-8')
            if not data:
                break
            print("Desde el usuario conectado: " + data)
            if data == 'get_video_list':
                videos = get_video_list(video_dir)
                c.send(json.dumps(videos).encode('utf-8'))
        c.close()

if __name__ == '__main__':
    main()
