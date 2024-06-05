import socket
import json
import argparse

def main(video_server_port):
    host = '192.168.0.8'
    port = 5000  # Este es el puerto en el que el servidor principal escucha

    s = socket.socket()
    s.bind((host, port))
    s.listen(1)

    print(f"Servidor principal escuchando en {host}:{port}")

    while True:
        c, addr = s.accept()
        print("Conexión desde: " + str(addr))
        while True:
            data = c.recv(1024).decode('utf-8')
            if not data:
                break
            print("Desde el usuario conectado: " + data)
            if data == 'get_video_list':
                video_server_host = 'localhost'
                video_server_socket = socket.socket()
                video_server_socket.connect((video_server_host, video_server_port))
                video_server_socket.send('get_video_list'.encode('utf-8'))
                videos = json.loads(video_server_socket.recv(1024).decode('utf-8'))
                video_server_socket.close()
                c.send(json.dumps(videos).encode('utf-8'))
        c.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Por favor, proporciona el puerto del servidor de videos como argumento al iniciar el servidor.")
    parser.add_argument('video_server_port', type=int, help='Puerto del servidor de videos')
    args = parser.parse_args()
    main(args.video_server_port)
