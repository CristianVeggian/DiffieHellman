import socket
import threading
import diffieHellman as dh

def send_messages(client_socket):
    while True:
        mensagem = input("Digite uma mensagem ou comando: ")
        if mensagem.lower() == 'sair':
            client_socket.close()
            print("CONEXÃO ENCERRADA!")
            break

        if '\\file' in mensagem:
            arq = mensagem[6:]
            with open(arq, 'r') as arquivo:
                msg = arquivo.read()
                meus_bytes = ('\\file '+ msg).encode() 
                client_socket.send(dh.encrypt_message(meus_bytes, dh.serialize_private_key(private_key)))
        else:
            # Envia a mensagem para o servidor
            client_socket.send(dh.encrypt_message(mensagem, dh.serialize_private_key(private_key)))

def receive_messages(client_socket):
    while True:
        # Recebe a resposta do servidor
        resposta = client_socket.recv(1024)
        print(f"Resposta do servidor: {resposta.decode()}")

# Configuração do cliente
host = '127.0.0.1'  # Endereço IP do servidor
port = 12345       # Porta em que o servidor está escutando

# Cria um socket do tipo TCP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conecta ao servidor
client_socket.connect((host, port))

mensagem = input("Digite seu nick: ")

private_key, public_key = dh.generate_dh_key_exchange(dh.generate_dh_parameters())

client_socket.send((dh.serialize_public_key(public_key) + mensagem).encode())
resposta = client_socket.recv(1024)
print(f"[SERVIDOR]: {resposta.decode()}")

send_thread = threading.Thread(target=send_messages, args=(client_socket,))
send_thread.start()

receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
receive_thread.start()
