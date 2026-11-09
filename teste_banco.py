
from database import conectar

try:
    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM USUARIO")

    print("Conexão realizada com sucesso!")
    print("Usuários cadastrados:", cursor.fetchall())

    con.close()

except Exception as erro:
    print("Erro ao conectar:", erro)
