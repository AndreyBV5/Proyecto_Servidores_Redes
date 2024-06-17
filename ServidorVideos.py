# Servidor de Videos
import os
import socket
import json
import argparse
import time
from threading import Thread, Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
from rich.table import Table

console = Console()

def get_video_list(video_dir):
    return [{'name': video, 'size': os.path.getsize(os.path.join(video_dir, video))}
            for video in os.listdir(video_dir) if os.path.isfile(os.path.join(video_dir, video))]

def display_video_list(videos):
    table = Table(title="Lista de Videos")

    table.add_column("Nombre", style="cyan", no_wrap=True)
    table.add_column("Tamaño (bytes)", style="magenta")

    for video in videos:
        table.add_row(video['name'], str(video['size']))

    console.print(table)

def display_server_info(video_server_host, port, video_dir, main_server_status):
    console.print(f"Servidor de video iniciado en {video_server_host}:{port}", style="bold yellow")
    
    table = Table(title="Información del Servidor de Videos")

    table.add_column("Parámetro", style="bold cyan", no_wrap=True)
    table.add_column("Valor", style="bold magenta")

    table.add_row("Host del Servidor de Videos", video_server_host)
    table.add_row("Puerto del Servidor de Videos", str(port))
    table.add_row("Directorio de Videos", video_dir)
    table.add_row("Estado del Servidor Principal", main_server_status)

    console.print(table)

def display_download_info(video_name, part_size, part_number, duration, video_size):
    table = Table(title="Descarga de Video")

    table.add_column("Nombre", style="bold cyan", no_wrap=True)
    table.add_column("Tamaño de la Parte (bytes)", style="bold magenta")
    table.add_column("Parte", style="bold green")
    table.add_column("Tiempo de Descarga (s)", style="bold yellow")

    part_info = "video completo" if part_size == video_size else str(part_number)
    table.add_row(video_name, str(part_size), part_info, f"{duration:.2f}")

    console.print(table)

class VideoDirectoryHandler(FileSystemEventHandler):
    def __init__(self, video_dir, main_server_host, main_server_port, video_server_info):
        self.video_dir = video_dir
        self.main_server_host = main_server_host
        self.main_server_port = main_server_port
        self.video_server_info = video_server_info

    def update_main_server(self):
        self.video_server_info['videos'] = get_video_list(self.video_dir)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.main_server_host, self.main_server_port))
            s.send(f"update_video_list|{json.dumps(self.video_server_info)}".encode('utf-8'))

    def on_created(self, event):
        self.update_main_server()

    def on_deleted(self, event):
        self.update_main_server()

def connect_to_main_server(main_server_host, main_server_port, video_server_info, stop_event):
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_server_socket:
                main_server_socket.connect((main_server_host, main_server_port))
                main_server_socket.send(json.dumps(video_server_info).encode('utf-8'))
                return "Conectado y registrado con éxito"
        except ConnectionRefusedError:
            stop_event.wait(2)
    return "Conexión rechazada, intentos agotados"

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
                        main_server_active = True
                        return "Activo"
                else:
                    raise ConnectionError("Respuesta inesperada del servidor principal.")
        except Exception as e:
            attempts += 1
            if attempts >= 3:
                stop_event.set()
                return "Caído"
        stop_event.wait(check_interval)
    if not main_server_active:
        stop_event.set()
        return "Caído"

def main():
    parser = argparse.ArgumentParser(description='Servidor de Videos')
    parser.add_argument('port', type=int, help='Puerto en que escucha el servidor')
    parser.add_argument('host', type=str, help='IP del servidor principal')
    parser.add_argument('video_dir', type=str, help='Ruta de la carpeta en que se almacenan los vídeos')

    args = parser.parse_args()
    port = args.port
    main_server_host = args.host
    video_dir = args.video_dir

    video_server_host = '172.17.47.138'  # IP del Servidor de Videos

    video_server_info = {
        'host': video_server_host,
        'port': port,
        'videos': get_video_list(video_dir)
    }

    stop_event = Event()

    connection_status = connect_to_main_server(main_server_host, 5000, video_server_info, stop_event)
    main_server_status = check_main_server_activity(main_server_host, 5000, 10, 30, stop_event)

    display_server_info(video_server_host, port, video_dir, main_server_status)

    observer = Observer()
    event_handler = VideoDirectoryHandler(video_dir, main_server_host, 5000, video_server_info)
    observer.schedule(event_handler, video_dir, recursive=True)
    observer.start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((video_server_host, port))
    s.listen(5)

    while not stop_event.is_set():
        c, addr = s.accept()

        data = c.recv(1024).decode('utf-8')

        if data == 'get_video_list':
            videos = get_video_list(video_dir)
            display_video_list(videos)
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
                display_download_info(video_name, part_size - bytes_remaining, part_number, duration, video_size)
            except FileNotFoundError:
                c.send(json.dumps({"error": f"No se encontró el video '{video_name}'"}).encode('utf-8'))
            except Exception as e:
                c.send(json.dumps({"error": "Error al procesar la solicitud"}).encode('utf-8'))

        c.close()

    s.close()
    observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
