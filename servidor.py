import socket
import threading

client_list = {}

def handle_messages(socket, endereco, nick):
    conn: socket.socket = socket
    username = nick

    while True:
        try:
            msg = conn.recv(1024)
        except ConnectionResetError:
            break

        if not msg:
            break

        msg_decoded = msg.decode()

        print(f"Received message from {username}")

        # Mensagens de Broadcast:
        if "\\broadcast " in msg_decoded:
            for chat_user in client_list.keys():
                if chat_user != nick:
                    cli_conn: socket.socket = client_list[chat_user][0]
                    try:
                        cli_conn.sendall(msg_decoded.encode())
                    except OSError:
                        pass
        elif "\\p " in msg_decoded:
            msg_decoded = msg_decoded[3:]
            destination = msg_decoded[:msg_decoded.index(" ")]
            msg_decoded = msg_decoded[msg_decoded.index(destination):]
            cli_conn: socket.socket = client_list[destination]
            try:
                cli_conn.send(msg_decoded.encode())
            except OSError:
                pass

    conn.close()

# Configuração do servidor
host = '127.0.0.1'  # Endereço IP do servidor
port = 12345       # Porta em que o servidor irá escutar
MAX_CHAT = 2

# Cria um socket do tipo TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Liga o socket ao endereço e porta especificados
server_socket.bind((host, port))

# Começa a escutar por conexões
server_socket.listen(MAX_CHAT)

print(f"Servidor escutando em {host}:{port}...")

while True:

    # Aceita uma conexão quando um cliente se conecta
    client_socket, client_address = server_socket.accept()

    print(f"Conexão estabelecida com {client_address}")
    # Recebe dados do cliente
    data = client_socket.recv(1024)
    
    dados = data.decode()

    key = dados[dados.index("-----BEGIN PUBLIC KEY-----"):dados.index("-----END PUBLIC KEY-----")]

    nick = dados[dados.index("-----END PUBLIC KEY-----")+25:]

    print(f"Novo cliente conectado: {nick}")

    client_list[nick] = (client_socket, key)

    client_socket.send("[CONECTADO]".encode())

    # Inicia a thread que vai receber as msgs dos clientes
    msg_thread = threading.Thread(target=handle_messages, args=(client_socket, client_address, data.decode(),), daemon=True)
    msg_thread.start()

# Fecha a conexão com o cliente e o servidor
client_socket.close()
server_socket.close()
