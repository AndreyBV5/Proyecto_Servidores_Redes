# Servidor de Videos
import os
import socket
import json
import argparse
import time

def get_video_list(video_dir):
    return [{'name': video, 'size': os.path.getsize(os.path.join(video_dir, video))}
            for video in os.listdir(video_dir) if os.path.isfile(os.path.join(video_dir, video))]

def main():
    parser = argparse.ArgumentParser(description='Servidor de Videos')
    parser.add_argument('port', type=int, help='Puerto en que escucha el servidor')
    parser.add_argument('host', type=str, help='IP del servidor principal')
    parser.add_argument('video_dir', type=str, help='Ruta de la carpeta en que se almacenan los vídeos')

    args = parser.parse_args()
    port = args.port
    main_server_host = args.host
    video_dir = args.video_dir

    video_server_host = '192.168.0.9'  # IP del Servidor de Videos

    print(f"Servidor de videos iniciado en {video_server_host}:{port}")
    print(f"Almacenando videos desde {video_dir}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((video_server_host, port))
    s.listen(5)

    # Conectar al Servidor Principal y enviar la lista de videos
    main_server_port = 5000  # Puerto del Servidor Principal
    main_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            main_server_socket.connect((main_server_host, main_server_port))
            break
        except ConnectionRefusedError:
            print("Conexión rechazada, intentando de nuevo en 5 segundos...")
            time.sleep(5)  # Espera 5 segundos antes de intentar de nuevo

    video_server_info = {
        'host': video_server_host,
        'port': port,
        'videos': get_video_list(video_dir)
    }
    main_server_socket.send(json.dumps(video_server_info).encode('utf-8'))
    main_server_socket.close()

    while True:
        c, addr = s.accept()
        print(f"Conexión desde: {addr}")

        data = c.recv(1024).decode('utf-8')
        print(f"Desde el usuario conectado: {data}")

        if data == 'get_video_list':
            videos = get_video_list(video_dir)
            c.send(json.dumps(videos).encode('utf-8'))
        else:
            try:
                video_name, part_number, part_size, video_size = data.split('|')
                part_number = int(part_number)
                part_size = int(part_size)
                video_size = int(video_size)
                video_path = os.path.join(video_dir, video_name)

                start_time = time.time()
                with open(video_path, 'rb') as video_file:
                    video_file.seek(part_number * part_size)
                    bytes_remaining = part_size
                    while bytes_remaining > 0:
                        chunk_size = min(1024, bytes_remaining)
                        chunk = video_file.read(chunk_size)
                        if not chunk:
                            break
                        c.send(chunk)
                        bytes_remaining -= len(chunk)
                end_time = time.time()
                duration = end_time - start_time
                print(f"Parte {part_number} descargada en {duration:.2f} segundos")
            except FileNotFoundError:
                c.send(json.dumps({"error": f"No se encontró el video '{video_name}'"}).encode('utf-8'))
            except Exception as e:
                print(f"Error al procesar la solicitud: {e}")
                c.send(json.dumps({"error": "Error al procesar la solicitud"}).encode('utf-8'))

        c.close()

if __name__ == '__main__':
    main()
