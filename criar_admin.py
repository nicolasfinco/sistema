
from database import conectar
from werkzeug.security import generate_password_hash
from getpass import getpass

nome = input("Nome do administrador: ")
email = input("E-mail: ")
senha = getpass("Senha: ")

senha_hash = generate_password_hash(senha)

con = conectar()
cursor = con.cursor()

try:
    cursor.execute("""
        INSERT INTO USUARIO (NOME, EMAIL, SENHA_HASH)
        VALUES (?, ?, ?)
    """, (nome, email, senha_hash))

    con.commit()
    print("Administrador cadastrado com sucesso!")

except Exception as erro:
    con.rollback()
    print("Erro ao cadastrar:", erro)

finally:
    con.close()
