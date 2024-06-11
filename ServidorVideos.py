# Servidor de Videos
import os
import socket
import json
import argparse
import time
from threading import Thread, Event

def get_video_list(video_dir):
    return [{'name': video, 'size': os.path.getsize(os.path.join(video_dir, video))}
            for video in os.listdir(video_dir) if os.path.isfile(os.path.join(video_dir, video))]

def connect_to_main_server(main_server_host, main_server_port, video_server_info, stop_event):
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_server_socket:
                main_server_socket.connect((main_server_host, main_server_port))
                main_server_socket.send(json.dumps(video_server_info).encode('utf-8'))
                print("Servidor principal conectado y registrado con éxito.")
                return
        except ConnectionRefusedError:
            print("Conexión rechazada, intentando de nuevo en 5 segundos...")
            stop_event.wait(2)
    print("Detenido intento de conexión al servidor principal.")

def check_main_server_activity(main_server_host, main_server_port, check_interval, timeout, stop_event):
    attempts = 0
    main_server_active = False
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_server_socket:
                main_server_socket.connect((main_server_host, main_server_port))
                main_server_socket.send(b'ping')
                response = main_server_socket.recv(1024).decode('utf-8')
                if response == 'pong':
                    if not main_server_active:
                        print("El servidor principal está activo.")
                    main_server_active = True
                    attempts = 0
                else:
                    raise ConnectionError("Respuesta inesperada del servidor principal.")
        except Exception as e:
            attempts += 1
            print(f"Intento {attempts}/3 fallido: {e}")
            if attempts >= 3:
                print("El servidor principal se considera caído. Cerrando el servidor de videos.")
                stop_event.set()
                break
        stop_event.wait(check_interval)
    if not main_server_active:
        print("El servidor principal no está activo. Cerrando el servidor de videos.")
        stop_event.set()

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

    video_server_info = {
        'host': video_server_host,
        'port': port,
        'videos': get_video_list(video_dir)
    }

    stop_event = Event()

    # Hilo para conectar al servidor principal y registrar el servidor de videos
    connection_thread = Thread(target=connect_to_main_server, args=(main_server_host, 5000, video_server_info, stop_event))
    connection_thread.start()

    # Hilo para verificar la actividad del servidor principal
    check_thread = Thread(target=check_main_server_activity, args=(main_server_host, 5000, 10, 30, stop_event))
    check_thread.start()

    while not stop_event.is_set():
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

    print("Servidor de videos cerrado debido a la caída del servidor principal.")
    s.close()

if __name__ == '__main__':
    main()