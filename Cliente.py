# Cliente
import socket
import json
import argparse
import os
from threading import Thread, Lock
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from time import time

console = Console()

def receive_message(s, buffer_size=1024):
    data = b''
    while True:
        part = s.recv(buffer_size)
        data += part
        if len(part) < buffer_size:
            break
    return data.decode('utf-8')

def download_part(server_info, video_name, part_number, part_size, video_size, progress, task_id, lock, total_parts):
    video_host, video_port = server_info
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as vs_socket:
        vs_socket.connect((video_host, video_port))
        vs_socket.send(f"{video_name}|{part_number}|{part_size}|{video_size}".encode('utf-8'))
        part_filename = f"{video_name}.part{part_number}" if total_parts > 1 else video_name
        with open(part_filename, 'wb') as f:
            downloaded = 0
            start_time = time()
            while True:
                chunk = vs_socket.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                with lock:
                    progress.update(task_id, advance=len(chunk))
            end_time = time()
    download_time = end_time - start_time
    if total_parts > 1:
        console.print(f"Parte {part_number} descargada. Tamaño: {downloaded} bytes. Tiempo: {download_time:.2f} segundos.")
    else:
        console.print(f"Video descargado. Tamaño: {downloaded} bytes. Tiempo: {download_time:.2f} segundos.")

def download_video(s, video_name, video_size, parts_info):
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
    )

    with progress:
        tasks = []
        total_parts = len(parts_info)
        for part_number, (server_info, part_size) in enumerate(parts_info):
            task_id = progress.add_task(
                f"[green]Descargando parte {part_number}..." if total_parts > 1 else "[green]Descargando video...",
                filename=f"{video_name} (parte {part_number})" if total_parts > 1 else video_name,
                total=part_size
            )
            tasks.append(task_id)

        lock = Lock()
        threads = []
        for part_number, (server_info, part_size) in enumerate(parts_info):
            thread = Thread(target=download_part, args=(server_info, video_name, part_number, part_size, video_size, progress, tasks[part_number], lock, total_parts))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    if total_parts > 1:
        with open(video_name, 'wb') as final_file:
            for part_number in range(len(parts_info)):
                part_filename = f"{video_name}.part{part_number}"
                with open(part_filename, 'rb') as part_file:
                    final_file.write(part_file.read())
                os.remove(part_filename)

    console.print(f"Video descargado como [bold green]{video_name}[/bold green]")

def main():
    parser = argparse.ArgumentParser(description="Cliente para acceder al servidor principal.")
    parser.add_argument('port', type=int, help='Puerto del servidor principal')
    parser.add_argument('host', type=str, help='IP del servidor principal')
    parser.add_argument('-l', '--lista', action='store_true', help='Mostrar lista de videos disponibles en el servidor principal')
    os.system('cls' if os.name == 'nt' else 'clear')
    parser.add_argument('-v', '--video', type=int, help='Número del video a descargar')
    args = parser.parse_args()

    port = args.port
    host = args.host
    show_video_list = args.lista
    video_number = args.video

    console.print(f"Conectando al servidor principal en [bold yellow]{host}:{port}[/bold yellow]")
    console.print("")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        if show_video_list:
            # Solicitar al servidor principal la lista de videos
            s.send('get_video_list'.encode('utf-8'))

            # Recibir la lista de videos del servidor principal
            data = receive_message(s)
            video_list = json.loads(data)

            # Mostrar la lista de videos usando rich
            table = Table(title="Lista de Videos Disponibles")
            table.add_column("Número", justify="right", style="cyan", no_wrap=True)
            table.add_column("Nombre", style="magenta")
            table.add_column("Tamaño (bytes)", justify="right", style="green")

            for idx, video in enumerate(video_list, start=1):
                table.add_row(str(idx), video['name'], str(video['size']))

            console.print(table)

        if video_number:
            # Solicitar la descarga del video
            s.send(f"download_video {video_number}".encode('utf-8'))

            # Recibir la confirmación con el nombre y tamaño del video
            video_data = receive_message(s)
            video_info = json.loads(video_data)
            if "error" in video_info:
                console.print(f"[bold red]Error:[/bold red] {video_info['error']}")
                return

            video_name = video_info["video_name"]
            video_size = video_info["video_size"]
            parts_info = video_info["parts_info"]

            # Descargar el video
            download_video(s, video_name, video_size, parts_info)
            
        s.close()
    except Exception as e:
        console.print(f"[bold red]Error al conectar al servidor principal:[/bold red] {e}")

if __name__ == '__main__':
    main()
