import socket
import threading
import re

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

        match = re.match(r"\[type:(\w+),dest:(\w+)(?:,name:(\w+\.\w+))?(?:,hash:(\w+))?,body:(.*?)\]", msg_decoded)

        type_value = match.group(1)
        dest_value = match.group(2)
        name_value = match.group(3)
        hash_value = match.group(4)
        body_value = match.group(5)

        print(msg_decoded)
        
        if type_value == 'text':
            msg = f'[type:text,orig:{nick},body:{body_value}]'
            cli_conn: socket.socket = client_list[dest_value]
            try:
                cli_conn.send(msg.encode())
            except OSError:
                pass
        elif type_value == 'file':
            msg = f'[type:file,orig:{nick},name:{name_value},hash:{hash_value},body:{body_value}]'
            cli_conn: socket.socket = client_list[dest_value]
            try:
                cli_conn.send(msg.encode())
            except OSError:
                pass
        elif type_value == 'par' or type_value == 'rpar':
            msg = f'[type:{type_value},orig:{nick},body:{body_value}]'
            cli_conn: socket.socket = client_list[dest_value]
            try:
                cli_conn.send(msg.encode())
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
    
    nick = data.decode()
    
    print(f"Novo cliente conectado: {nick}")

    client_list[nick] = client_socket

    client_socket.send("Conectado ao chat".encode())

    # Inicia a thread que vai receber as msgs dos clientes
    msg_thread = threading.Thread(target=handle_messages, args=(client_socket, client_address, nick,), daemon=True)
    msg_thread.start()

# Fecha a conexão com o cliente e o servidor
client_socket.close()
server_socket.close()
