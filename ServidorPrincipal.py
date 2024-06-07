import socket
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description="Por favor, proporciona el puerto del servidor principal como argumento al iniciar el servidor.")
    parser.add_argument('port', type=int, help='Puerto del servidor principal')
    args = parser.parse_args()

    port = args.port
    host = '192.168.0.9'  # IP del Servidor Principal

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)  # Permitir múltiples conexiones

    print(f"Servidor principal escuchando en {host}:{port}")

    while True:
        c, addr = s.accept()
        print("Conexión desde: " + str(addr))
        data = c.recv(1024).decode('utf-8')
        if not data.strip():
            c.close()
            continue

        print("Desde el usuario conectado: " + data)

        if data.startswith('get_video_list'):
            video_server_host = 'localhost'  # IP del servidor de videos
            video_server_port = 5001  # Puerto del servidor de videos
            video_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                video_server_socket.connect((video_server_host, video_server_port))
                video_server_socket.send('get_video_list'.encode('utf-8'))
                videos = video_server_socket.recv(1024).decode('utf-8')
                video_server_socket.close()
                print("Videos recibidos del servidor de videos: " + videos)
                c.send(videos.encode('utf-8'))  # Envía la lista de videos al cliente
            except Exception as e:
                print(f"Error al conectar con el servidor de videos: {e}")
                c.send(json.dumps({"error": "No se pudo conectar al servidor de videos"}).encode('utf-8'))
        else:
            c.send(json.dumps({"error": "Solicitud no válida"}).encode('utf-8'))

        c.close()

if __name__ == '__main__':
    main()
