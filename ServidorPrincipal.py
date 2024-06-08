import socket
import json

def main():
    port = 5000
    host = '192.168.0.9'  # Cambia esta IP según sea necesario

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    print(f"Servidor principal escuchando en {host}:{port}")

    video_server_info = None

    while True:
        c, addr = s.accept()
        print("Conexión desde: " + str(addr))
        data = c.recv(1024).decode('utf-8')
        if not data:
            c.close()
            continue

        print("Desde el usuario conectado: " + data)

        if data == 'get_video_list':
            if video_server_info:
                c.send(json.dumps(video_server_info['videos']).encode('utf-8'))
            else:
                c.send(json.dumps({"error": "No hay servidores de video disponibles"}).encode('utf-8'))
        elif data.startswith('download_video'):
            video_number = int(data.split()[1])
            if video_server_info and 0 < video_number <= len(video_server_info['videos']):
                video_name = video_server_info['videos'][video_number - 1]
                video_host = video_server_info['host']
                video_port = video_server_info['port']
                
                # Conectar al Servidor de Videos
                vs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                vs_socket.connect((video_host, video_port))
                vs_socket.send(video_name.encode('utf-8'))

                # Confirmar el nombre del video al cliente
                c.send(json.dumps({"video_name": video_name}).encode('utf-8'))

                # Recibir el video en partes y reenviar al cliente
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
                print(f"Servidor de videos conectado: {video_server_info}")
                c.send(json.dumps({"status": "Servidor de videos registrado con éxito"}).encode('utf-8'))
            except json.JSONDecodeError as e:
                print(f"Error al decodificar JSON: {e}")

        c.close()

if __name__ == '__main__':
    main()
