
from firebird.driver import connect

def conectar():
    return connect(
        database=r'C:\Users\Aluno\Downloads\BANCO (2)\BANCO.FDB',
        user='SYSDBA',
        password='sysdba',
        charset='UTF8'
    )
