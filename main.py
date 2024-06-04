import socket
import threading
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 12345))
server_socket.listen(5)
clients = []

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                r.lpush('chat_messages', message)
                print(f"Отримано повідомлення: {message}")

                for client in clients:
                    if client != client_socket:
                        client.send(message.encode('utf-8'))
            else:
                break
        except:
            clients.remove(client_socket)
            client_socket.close()
            break

while True:
    client_socket, client_add = server_socket.accept()
    clients.append(client_socket)
    print(f"Підключено клієнта: {client_add}")
    threading.Thread(target=handle_client, args=(client_socket,)).start()
