import socket
import json
import argparse

def main():
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description="Por favor, proporciona el puerto del servidor principal como argumento al iniciar el servidor.")
    parser.add_argument('port', type=int, help='Puerto del servidor principal')
    args = parser.parse_args()

    port = args.port

    host = '192.168.0.8'

    s = socket.socket()
    s.bind((host, port))
    s.listen(1)

    print(f"Servidor principal escuchando en {host}:{port}")

    video_server_info = None

    while True:
        c, addr = s.accept()
        print("Conexión desde: " + str(addr))
        data = c.recv(1024).decode('utf-8')
        if not data.strip():  # Verificar si la cadena recibida no está vacía antes de intentar cargarla como JSON
            continue

        print("Desde el usuario conectado: " + data)
        
        try:
            message = json.loads(data)
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {e}")
            continue
        if isinstance(message, dict) and 'port' in message and 'videos' in message and 'host' in message:
            # Guardar la información del servidor de videos
            video_server_info = {
                'host': message['host'],  # IP del servidor de videos
                'port': message['port'],
                'videos': message['videos']
            }
            print(f"Información del servidor de videos recibida: {video_server_info}")

            # Enviar la información del servidor principal al servidor de videos
            main_server_info = {
                'host': host,
                'port': port
            }
            c.send(json.dumps(main_server_info).encode('utf-8'))
        else:
            if data == 'get_video_list' and video_server_info:
                # Conectar al servidor de videos usando la información almacenada
                video_server_host = video_server_info['host']
                video_server_port = video_server_info['port']
                video_server_socket = socket.socket()
                video_server_socket.connect((video_server_host, video_server_port))
                video_server_socket.send('get_video_list'.encode('utf-8'))
                videos = json.loads(video_server_socket.recv(1024).decode('utf-8'))
                video_server_socket.close()
                c.send(json.dumps(videos).encode('utf-8'))
        c.close()

if __name__ == '__main__':
    main()