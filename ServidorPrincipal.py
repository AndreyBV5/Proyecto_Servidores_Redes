# Servidor Principal
import socket
import json
import argparse
from rich.console import Console
from rich.table import Table

console = Console()

def display_server_info(video_servers):
    table = Table(title="Servidores de Videos Conectados")

    table.add_column("Host", style="cyan", no_wrap=True)
    table.add_column("Port", style="magenta")
    table.add_column("Videos", style="green")

    for server, info in video_servers.items():
        videos = ", ".join([video['name'] for video in info['videos']])
        table.add_row(server[0], str(server[1]), videos)

    console.print(table)

def main(port):
    host = '172.17.47.138'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    console.print(f"\nServidor principal escuchando en [bold green]{host}:{port}[/bold green]\n")

    video_servers = {}
    client_addresses = set()

    while True:
        c, addr = s.accept()
        data = c.recv(1024).decode('utf-8')
        if not data:
            c.close()
            continue

        if addr not in client_addresses and data != 'ping':
            console.print(f"[bold yellow]Conexión desde:[/bold yellow] {addr}")
            client_addresses.add(addr)
        
        if data == 'get_video_list':
            all_videos = {}
            for server, info in video_servers.items():
                for video in info['videos']:
                    video_key = (video['name'], video['size'])
                    if video_key not in all_videos:
                        all_videos[video_key] = {'name': video['name'], 'size': video['size'], 'server': server}
            c.send(json.dumps(list(all_videos.values())).encode('utf-8'))
        elif data.startswith('download_video'):
            video_number = int(data.split()[1])
            all_videos = {}
            for server, info in video_servers.items():
                for video in info['videos']:
                    video_key = (video['name'], video['size'])
                    if video_key not in all_videos:
                        all_videos[video_key] = {'name': video['name'], 'size': video['size'], 'server': server}
            
            all_videos_list = list(all_videos.values())
            if 0 < video_number <= len(all_videos_list):
                video_info = all_videos_list[video_number - 1]
                video_name, video_size, server = video_info['name'], video_info['size'], video_info['server']

                servers_with_video = [s for s in video_servers if any(v['name'] == video_name for v in video_servers[s]['videos'])]
                num_servers = len(servers_with_video)
                part_size = video_size // num_servers

                parts_info = []
                for i, server in enumerate(servers_with_video):
                    video_host, video_port = video_servers[server]['host'], video_servers[server]['port']
                    parts_info.append(((video_host, video_port), part_size))

                c.send(json.dumps({"video_name": video_name, "video_size": video_size, "parts_info": parts_info}).encode('utf-8'))
            else:
                c.send(json.dumps({"error": "Número de video inválido"}).encode('utf-8'))
        elif data == 'ping':
            c.send('pong'.encode('utf-8'))
        elif data.startswith('update_video_list'):
            try:
                command, video_server_info_str = data.split('|', 1)
                video_server_info = json.loads(video_server_info_str)
                video_servers[(video_server_info['host'], video_server_info['port'])] = video_server_info
                c.send(json.dumps({"status": "Lista de videos actualizada con éxito"}).encode('utf-8'))
                display_server_info(video_servers)
            except ValueError as e:
                console.print(f"Error al decodificar JSON: {e}", style="bold red")
                c.send(json.dumps({"error": "Error al decodificar JSON"}).encode('utf-8'))
        else:
            try:
                video_server_info = json.loads(data)
                video_servers[(addr[0], video_server_info['port'])] = video_server_info
                c.send(json.dumps({"status": "Servidor de videos registrado con éxito"}).encode('utf-8'))
                display_server_info(video_servers)
            except json.JSONDecodeError as e:
                console.print(f"Error al decodificar JSON: {e}", style="bold red")

        c.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Servidor Principal")
    parser.add_argument("port", type=int, help="Puerto en el que escucha el servidor")
    args = parser.parse_args()
    main(args.port)
