# Servidor Principal
import socket
import json
import argparse

def main(port):
    host = '192.168.0.9'  # Cambia esta IP según sea necesario

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    print(f"Servidor principal escuchando en {host}:{port}")

    video_servers = {}

    while True:
        c, addr = s.accept()
        print("Conexión desde: " + str(addr))
        data = c.recv(1024).decode('utf-8')
        if not data:
            c.close()
            continue

        print("Desde el usuario conectado: " + data)

        if data == 'get_video_list':
            unique_videos = {}
            for server, info in video_servers.items():
                for video in info['videos']:
                    if video['name'] not in unique_videos:
                        unique_videos[video['name']] = {'name': video['name'], 'size': video['size'], 'server': server}

            all_videos = list(unique_videos.values())
            c.send(json.dumps(all_videos).encode('utf-8'))
        elif data.startswith('download_video'):
            video_number = int(data.split()[1])
            unique_videos = {}
            for server, info in video_servers.items():
                for video in info['videos']:
                    if video['name'] not in unique_videos:
                        unique_videos[video['name']] = {'name': video['name'], 'size': video['size'], 'server': server}

            all_videos = list(unique_videos.values())

            if 0 < video_number <= len(all_videos):
                video_info = all_videos[video_number - 1]
                video_name, video_size, server = video_info['name'], video_info['size'], video_info['server']

                # Obtener los servidores que tienen este video
                servers_with_video = [s for s in video_servers if any(v['name'] == video_name for v in video_servers[s]['videos'])]
                num_servers = len(servers_with_video)
                part_size = video_size // num_servers

                c.send(json.dumps({"video_name": video_name, "video_size": video_size, "parts": num_servers}).encode('utf-8'))

                for i, server in enumerate(servers_with_video):
                    video_host, video_port = video_servers[server]['host'], video_servers[server]['port']
                    
                    # Conectar al Servidor de Videos
                    vs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    vs_socket.connect((video_host, video_port))
                    vs_socket.send(f"{video_name}|{i}|{part_size}".encode('utf-8'))

                    # Recibir la parte del video y reenviar al cliente
                    while True:
                        chunk = vs_socket.recv(1024)
                        if not chunk:
                            break
                        c.send(chunk)
                    
                    vs_socket.close()
            else:
                c.send(json.dumps({"error": "Número de video inválido"}).encode('utf-8'))
        else:
            # Manejo de conexión desde el Servidor de Videos
            try:
                video_server_info = json.loads(data)
                video_servers[addr] = video_server_info
                print(f"Servidor de videos conectado: {video_server_info}")
                c.send(json.dumps({"status": "Servidor de videos registrado con éxito"}).encode('utf-8'))
            except json.JSONDecodeError as e:
                print(f"Error al decodificar JSON: {e}")

        c.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Servidor Principal")
    parser.add_argument("port", type=int, help="Puerto en el que escucha el servidor")
    args = parser.parse_args()
    main(args.port)
