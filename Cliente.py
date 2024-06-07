import socket
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description="Cliente para acceder al servidor principal.")
    parser.add_argument('port', type=int, help='Puerto del servidor principal')
    parser.add_argument('host', type=str, help='IP del servidor principal')
    parser.add_argument('-l', '--lista', action='store_true', help='Mostrar lista de videos disponibles en el servidor principal')
    args = parser.parse_args()

    port = args.port
    host = args.host
    show_video_list = args.lista

    print(f"Conectando al servidor principal en {host}:{port}")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        if show_video_list:
            # Solicitar al servidor principal la lista de videos
            s.send('get_video_list'.encode('utf-8'))

            # Recibir la lista de videos del servidor principal
            data = s.recv(1024).decode('utf-8')
            video_list = json.loads(data)

            # Mostrar la lista de videos
            print("Lista de videos disponibles:")
            for video in video_list:
                print(video)

        s.close()
    except Exception as e:
        print(f"Error al conectar al servidor principal: {e}")

if __name__ == '__main__':
    main()
