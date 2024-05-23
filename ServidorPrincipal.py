# Servidor Principal
import socket
import json

def main():
    host = 'localhost'
    port = 5000

    s = socket.socket()
    s.bind((host, port))

    s.listen(1)
    while True:
        c, addr = s.accept()
        print("Connection from: " + str(addr))
        while True:
            data = c.recv(1024).decode('utf-8')
            if not data:
                break
            print("from connected user: " + data)
            if data == 'get_video_list':
                video_server_host = 'localhost'
                video_server_port = 5001
                video_server_socket = socket.socket()
                video_server_socket.connect((video_server_host, video_server_port))
                video_server_socket.send('get_video_list'.encode('utf-8'))
                videos = json.loads(video_server_socket.recv(1024).decode('utf-8'))
                video_server_socket.close()
                c.send(json.dumps(videos).encode('utf-8'))
        c.close()

if __name__ == '__main__':
    main()
