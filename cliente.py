import socket
import threading
import re
import random
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

pares = {}

def encrypt_text(plaintext: str, password: str):
    backend = default_backend()
    key = password.encode() + (32 * b"\x00")
    key = key[:32]
    iv = b"\x00" * 16
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=backend)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    ciphertext = base64.b16encode(ciphertext).decode("utf-8")
    return ciphertext

def decrypt_text(ciphertext: str, password: str):
    ciphertext = base64.b16decode(ciphertext)
    backend = default_backend()
    key = password.encode() + (32 * b"\x00")
    key = key[:32]
    iv = b"\x00" * 16
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=backend)
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode()

def receive_messages(client_socket, Kpl, Kpr, p):
    while True:
        try:
            msg = client_socket.recv(1024)
        except ConnectionResetError:
            break

        match = re.match(r"\[type:(\w+),orig:(\w+)(?:,name:(\w+\.\w+))?(?:,hash:(\w+))?,body:(.*?)\]", msg.decode())

        type_value = match.group(1)
        orig_value = match.group(2)
        name_value = match.group(3)
        hash_value = match.group(4)
        body_encrypted_value = match.group(5)

        if type_value == 'text':
            #descriptografar o body aqui
            secret_key = pares[orig_value]**Kpr % p
            body = decrypt_text(body_encrypted_value, f'{secret_key}')
            print(f'[{orig_value}] disse: {body}')
        elif type_value == 'file':
            with open(name_value, 'w') as arquivo:
                #descriptografar o body aqui
                secret_key = pares[orig_value]**Kpr % p
                body = decrypt_text(body_encrypted_value, f'{secret_key}')
                #Conferir se hash recebida bate com a hash gerada
                h = hashlib.new('sha256')
                h.update(body.encode())
                file_hash = h.hexdigest()
                if file_hash == hash_value:
                    print(f'[{orig_value}] te enviou o arquivo "{name_value}"')
                    arquivo.write(body)
                else:
                    print("[SISTEMA] Arquivo com integridade comprometida. Não foi salvo.")
        elif type_value == 'par':
            pares[orig_value] = int(body_encrypted_value)
            resp = f'[type:rpar,dest:{orig_value},body:{Kpl}]'
            client_socket.send(resp.encode())
            print(pares)
        elif type_value == 'rpar':
            pares[orig_value] = int(body_encrypted_value)
            print(pares)

# Configuração do cliente
host = '127.0.0.1'  # Endereço IP do servidor
port = 12345       # Porta em que o servidor está escutando

# Cria um socket do tipo TCP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conecta ao servidor
client_socket.connect((host, port))

mensagem = input("Digite seu nick: ")

#diffie-hellmann

if 'Alice' in mensagem:
    Kpr = 15
elif 'Bob' in mensagem:
    Kpr = 13
else:
    Kpr = random.randint(1, 100)

p = 17
g = 3

Kpl = g**Kpr % p

client_socket.send(f'{mensagem}'.encode())
resposta = client_socket.recv(1024)
print(f"[SERVIDOR]: {resposta.decode()}")

receive_thread = threading.Thread(target=receive_messages, args=(client_socket,Kpl,Kpr,p), daemon=True)
receive_thread.start()

while True:
    header = ''
    mensagem = input("Digite uma mensagem ou comando: ")
    if mensagem.lower() == '\\sair':
        client_socket.close()
        print("CONEXÃO ENCERRADA!")
        break
    elif '\\par' in mensagem:
        args = mensagem.split(maxsplit=2)
        header = f'[type:par,dest:{args[1]},body:{Kpl}]'
        client_socket.send(header.encode())
    elif '\\file' in mensagem:
        args = mensagem.split(maxsplit=2)
        if len(args) == 3:
            if args[1] in pares.keys():
                with open(args[2], 'r') as arquivo:
                    body = arquivo.read()
                    #GERAR HASH PARA CONFERIR INTEGRIDADE
                    h = hashlib.new('sha256')
                    h.update(body.encode())
                    file_hash = h.hexdigest()
                    #CRIPTOGRAFAR BODY AQUI
                    secret_key = pares[args[1]]**Kpr % p
                    body_cript = encrypt_text(body, f'{secret_key}')
                    header = f'[type:file,dest:{args[1]},name:{args[2]},hash:{file_hash},body:{body_cript}]'
                    client_socket.send(header.encode())
            else:
                print("Você precisa se parear com alguém para realizar a troca de chaves.\nUse o comando \\par -nome-")
        else:
            print("[SISTEMA] Formato Incorreto")
    elif '\\p' in mensagem:
        args = mensagem.split(maxsplit=2)
        if len(args) == 3:
            if args[1] in pares.keys():
                body = args[2]
                #CRIPTOGRAFAR BODY AQUI
                secret_key = pares[args[1]]**Kpr % p
                body_cript = encrypt_text(body, f'{secret_key}')
                header = f'[type:text,dest:{args[1]},body:{body_cript}]'
                client_socket.send(header.encode())
            else:
                print("[SISTEMA] Destino não encontrado \nUse o comando \\par -nome-")
        else:
            print("[SISTEMA] Formato Incorreto")
    else:
        print("[SISTEMA] Comando não reconhecido")
