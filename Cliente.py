import socket
import json
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Cliente para acceder al servidor principal.")
    parser.add_argument('port', type=int, help='Puerto del servidor principal')
    parser.add_argument('host', type=str, help='IP del servidor principal')
    parser.add_argument('-l', '--lista', action='store_true', help='Mostrar lista de videos disponibles en el servidor principal')
    parser.add_argument('-v', '--video', type=int, help='Número del video a descargar')
    args = parser.parse_args()

    port = args.port
    host = args.host
    show_video_list = args.lista
    video_number = args.video

    print(f"Conectando al servidor principal en {host}:{port}")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        if show_video_list:
            # Solicitar al servidor principal la lista de videos
            s.send('get_video_list'.encode('utf-8'))

            # Recibir la lista de videos del servidor principal
            data = s.recv(1024).decode('utf-8')
            video_list = json.loads(data)

            # Mostrar la lista de videos
            print("Lista de videos disponibles:")
            for idx, video in enumerate(video_list, start=1):
                print(f"{idx}. {video}")

        if video_number:
            # Solicitar la descarga del video
            s.send(f"download_video {video_number}".encode('utf-8'))

            # Recibir la confirmación con el nombre del video
            video_data = s.recv(1024).decode('utf-8')
            video_info = json.loads(video_data)
            if "error" in video_info:
                print(video_info["error"])
                return

            video_name = video_info["video_name"]
            with open(video_name, 'wb') as f:
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    f.write(chunk)

            print(f"Video descargado como {video_name}")

        s.close()
    except Exception as e:
        print(f"Error al conectar al servidor principal: {e}")

if __name__ == '__main__':
    main()
