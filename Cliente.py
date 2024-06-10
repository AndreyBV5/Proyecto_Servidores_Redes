# Cliente
import socket
import json
import argparse
import time
from tqdm import tqdm

def receive_message(s, buffer_size=1024):
    data = b''
    while True:
        part = s.recv(buffer_size)
        data += part
        if len(part) < buffer_size:
            break
    return data.decode('utf-8')

def download_video(s, video_name, video_size, num_parts):
    with open(video_name, 'wb') as f:
        downloaded = 0
        start_time = time.time()
        
        with tqdm(total=video_size, unit='B', unit_scale=True, desc=video_name, ascii=True) as pbar:
            for part in range(num_parts):
                part_start_time = time.time()
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    pbar.update(len(chunk))
                part_end_time = time.time()
                part_duration = part_end_time - part_start_time
                print(f"Parte {part} descargada en {part_duration:.2f} segundos")
        
        end_time = time.time()
        total_duration = end_time - start_time
        print(f"Video descargado como {video_name}")
        print(f"Tiempo total de descarga: {total_duration:.2f} segundos")

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
            data = receive_message(s)
            video_list = json.loads(data)

            # Mostrar la lista de videos
            print("Lista de videos disponibles:")
            for idx, video in enumerate(video_list, start=1):
                print(f"{idx}. {video['name']} - {video['size']} bytes")

        if video_number:
            # Solicitar la descarga del video
            s.send(f"download_video {video_number}".encode('utf-8'))

            # Recibir la confirmación con el nombre y tamaño del video
            video_data = receive_message(s)
            video_info = json.loads(video_data)
            if "error" in video_info:
                print(video_info["error"])
                return

            video_name = video_info["video_name"]
            video_size = video_info["video_size"]
            num_parts = video_info["parts"]

            # Descargar el video
            download_video(s, video_name, video_size, num_parts)

        s.close()
    except Exception as e:
        print(f"Error al conectar al servidor principal: {e}")

if __name__ == '__main__':
    main()







