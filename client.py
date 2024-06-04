import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"Отримано повідомлення: {message}")
        except:
            print("З'єднання з сервером втрачено.")
            break

def send_messages(client_socket):
    while True:
        message = input("Введіть повідомлення: ")
        client_socket.send(message.encode('utf-8'))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 12345))

threading.Thread(target=receive_messages, args=(client_socket,)).start()
send_messages(client_socket)
