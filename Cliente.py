# Cliente
import socket

def main():
    host = '192.168.0.8'
    port = 5001

    s = socket.socket()
    s.connect((host, port))

    while True:
        print("Menu:")
        print("v - Mostrar lista de videos")
        print("0 - Salir")
        option = input("Ingrese su opción: ")
        if option.lower() == 'v':
            s.send('get_video_list'.encode('utf-8'))
            data = s.recv(1024).decode('utf-8')
            print("Lista de videos: " + data)
        elif option == '0':
            print("Saliendo...")
            break
        else:
            print("Opción no reconocida. Por favor, intente de nuevo.")

    s.close()

if __name__ == '__main__':
    main()
