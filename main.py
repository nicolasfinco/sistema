import locale
from flask import Flask, render_template, request, redirect, url_for, flash,  session
from datetime import datetime, date
from database import conectar
from werkzeug.security import check_password_hash

# mudando idioma do sistema para portugues
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'portuguese_brazil')

# "banco" de dados
usuarios = [{'id': 0, 'nome': "Paulo",  'email': "paulo@email", 'tel': "18991456464", 'cpf': "41317641809", 'senha': "@Senai123"}]
pets = [{'id': 0, 'nome': "Bach", 'donoId': 0, 'raca': "Gato", 'peso': 5000, 'idade': 10 }]
consultas = []
usuario_atual = None
base_fluido = 50

# lista p opções de atendimento
opcoes_atend = [
    "Banho",
    "Vacinação",
    "Consulta",
    "Exames",
    "Odonto", 
    "Fisioterapia",
    "Atendimento domiciliar"
]

# lista de opções de espécies
opcoes_especies = {
    "Cão",
    "Gato",
    "Pássaro",
    "Peixe",
    "Tartaruga"
}

app = Flask(__name__)
app.secret_key = 'minha-chave-secreta' # chave secreta para a sessão e flash


def encontrar_user(email):
    con = conectar()

    try:
        cursor = con.cursor()

        cursor.execute("""
            SELECT ID_USUARIO, NOME, EMAIL, SENHA_HASH, ATIVO
            FROM USUARIO
            WHERE EMAIL = ?
        """, (email,))

        resultado = cursor.fetchone()

        if resultado:
            return {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'senha_hash': resultado[3],
                'ativo': resultado[4]
            }

        return None

    finally:
        con.close()


def encontrar_pets(userId):
    encontrados = []
    for p in pets:
        if p['donoId']:
            if p['donoId'] == userId:
                encontrados.append(p)
    return encontrados

def encontrar_pet(id):
    for p in pets:
        if p['id'] == int(id):
            return p

def obter_lista_relacionada(lista, buscarPor, id):
    encontrados = []
    for n in lista:
        if n[buscarPor] == id:
            encontrados.append(n)
    return encontrados

def obter_item(lista, id):
    for item in lista:
        if item['id'] == id:
            return item

def gerar_id(lista):
    id = 0
    for p in lista:
        if p['id'] == id:
            id = p['id'] + 1
    return id

# rota para home
@app.route('/')
def index():
    return render_template('index.html', usuario=usuario_atual)

# login e cadastro do usuario
@app.route('/login', methods=["GET", "POST"])

@app.route('/login', methods=["GET", "POST"])
def login():
    global usuario_atual

    if session.get('usuario_id'):
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template('login.html')

    try:
        email = request.form['email']
        senha = request.form['senha']

        user = encontrar_user(email)

        if user is None:
            flash('E-mail ou senha incorretos', 'warning')
            return redirect(url_for('login'))

        if not user['ativo']:
            flash('Usuário desativado', 'warning')
            return redirect(url_for('login'))

        if not check_password_hash(user['senha_hash'], senha):
            flash('E-mail ou senha incorretos', 'warning')
            return redirect(url_for('login'))

        session.clear()
        session['usuario_id'] = user['id']
        session['usuario_nome'] = user['nome']

        # Compatibilidade temporária com as rotas antigas
        usuario_atual = {
            'id': user['id'],
            'nome': user['nome'],
            'email': user['email']
        }

        flash('Login realizado com sucesso!', 'success')

        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f'Erro no login: {e}')
        flash('Erro ao realizar login', 'error')
        return redirect(url_for('login'))


# rota de cadastro

@app.route('/editar_tutor/<int:id>', methods=['GET', 'POST'])
def editar_tutor(id):
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        if request.method == 'GET':
            cursor.execute("""
                SELECT ID_TUTOR, NOME, CPF, TELEFONE, EMAIL, ENDERECO
                FROM TUTOR
                WHERE ID_TUTOR = ?
            """, (id,))

            tutor = cursor.fetchone()

            if not tutor:
                flash('Tutor não encontrado.', 'warning')
                return redirect(url_for('tutores'))

            return render_template('editarTutor.html', tutor=tutor)

        nome = request.form['nome'].strip()
        cpf = request.form['cpf'].strip()
        telefone = request.form['tel'].strip()
        email = request.form.get('email', '').strip() or None
        endereco = request.form.get('endereco', '').strip() or None

        cursor.execute("""
            SELECT ID_TUTOR FROM TUTOR
            WHERE CPF = ? AND ID_TUTOR <> ?
        """, (cpf, id))

        if cursor.fetchone():
            flash('Esse CPF já pertence a outro tutor.', 'warning')
            return redirect(url_for('editar_tutor', id=id))

        cursor.execute("""
            UPDATE TUTOR
            SET NOME = ?, CPF = ?, TELEFONE = ?, EMAIL = ?, ENDERECO = ?
            WHERE ID_TUTOR = ?
        """, (nome, cpf, telefone, email, endereco, id))

        con.commit()
        flash('Tutor atualizado com sucesso!', 'success')
        return redirect(url_for('tutores'))

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao editar tutor: {e}')
        flash('Erro ao editar tutor.', 'error')
        return redirect(url_for('tutores'))

    finally:
        if con:
            con.close()


@app.route('/remover_tutor/<int:id>', methods=['POST'])
def remover_tutor(id):
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM PET WHERE ID_TUTOR = ?
        """, (id,))

        quantidade_pets = cursor.fetchone()[0]

        if quantidade_pets > 0:
            flash('Não é possível excluir: esse tutor possui pets cadastrados.', 'warning')
            return redirect(url_for('tutores'))

        cursor.execute("""
            DELETE FROM TUTOR WHERE ID_TUTOR = ?
        """, (id,))

        con.commit()
        flash('Tutor removido com sucesso!', 'success')

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao remover tutor: {e}')
        flash('Erro ao remover tutor.', 'error')

    finally:
        if con:
            con.close()

    return redirect(url_for('tutores'))


@app.route('/tutores')
def tutores():
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        cursor.execute("""
            SELECT ID_TUTOR, NOME, CPF, TELEFONE, EMAIL, ENDERECO
            FROM TUTOR
            ORDER BY NOME
        """)

        tutores = cursor.fetchall()

        return render_template('tutores.html', tutores=tutores)

    except Exception as e:
        print(f'Erro ao listar tutores: {e}')
        flash('Erro ao carregar tutores.', 'error')
        return redirect(url_for('dashboard'))

    finally:
        if con:
            con.close()


@app.route('/cadastrar_tutor', methods=['GET', 'POST'])
def cadastrar_tutor():
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('cadastrarTutor.html')

    nome = request.form['nome'].strip()
    cpf = request.form['cpf'].strip()
    telefone = request.form['tel'].strip()
    email = request.form.get('email', '').strip() or None
    endereco = request.form.get('endereco', '').strip() or None

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        cursor.execute(
            "SELECT ID_TUTOR FROM TUTOR WHERE CPF = ?",
            (cpf,)
        )

        if cursor.fetchone():
            flash('Já existe um tutor com esse CPF.', 'warning')
            return redirect(url_for('cadastrar_tutor'))

        cursor.execute("""
            INSERT INTO TUTOR (NOME, CPF, TELEFONE, EMAIL, ENDERECO)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, cpf, telefone, email, endereco))

        con.commit()

        flash('Tutor cadastrado com sucesso!', 'success')
        return redirect(url_for('tutores'))

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao cadastrar tutor: {e}')
        flash('Erro ao cadastrar tutor.', 'error')
        return redirect(url_for('cadastrar_tutor'))

    finally:
        if con:
            con.close()

#rota de  ar o cadastro do usuario
@app.route('/editar_usuario', methods=["GET", "POST"])
def edcadastro():
    try:
        global usuario_atual
        if usuario_atual == None:
            return redirect(url_for('login'))
        
        if request.method == "POST":
            vai_redirecionar = False

            for u in usuarios:
                if u != usuario_atual:
                    if u['cpf'] == request.form['cpf']:
                        flash('CPF já cadastrado', 'warning')
                        vai_redirecionar = True
                    if u['email'] == request.form['email']:
                        flash('E-mail já cadastrado', 'warning')
                        vai_redirecionar = True
                    if vai_redirecionar == True:
                        return redirect(url_for('cadastrar'))

            for n in request.form:
                if n in usuario_atual:
                    usuario_atual[n] = request.form[n]

            return redirect(url_for('dashboard'))
    except Exception as e:
        flash('Houve um erro ao editar usuário', 'error')
    return render_template('editarUser.html', usuario=usuario_atual)

# rota de logout para sair da conta do usuário
@app.route('/logout')
def logout():
    global usuario_atual

    session.clear()
    usuario_atual = None

    flash('Você saiu do sistema', 'success')

    return redirect(url_for('login'))

# cadastro de pet
def listar_tutores_para_pet(cursor):
    cursor.execute("""
        SELECT ID_TUTOR, NOME
        FROM TUTOR
        ORDER BY NOME
    """)
    return cursor.fetchall()


@app.route('/cadastrar_pet', methods=['GET', 'POST'])
def cadastrar_pet():
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        tutores = listar_tutores_para_pet(cursor)

        if request.method == 'GET':
            return render_template(
                'cadastrarPet.html',
                tutores=tutores,
                especies=opcoes_especies
            )

        nome = request.form['nome'].strip()
        tutor_id = int(request.form['tutor'])
        especie = request.form['especie']
        raca = request.form['raca'].strip()
        sexo = request.form['sexo']
        nascimento = date.fromisoformat(request.form['data_nascimento'])
        observacoes = request.form.get('observacoes', '').strip() or None

        if sexo not in ('MACHO', 'FEMEA'):
            flash('Selecione um sexo válido.', 'warning')
            return redirect(url_for('cadastrar_pet'))

        cursor.execute("""
            INSERT INTO PET
                (ID_TUTOR, NOME, ESPECIE, RACA, SEXO,
                 DATA_NASCIMENTO, OBSERVACOES)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tutor_id, nome, especie, raca, sexo,
            nascimento, observacoes
        ))

        con.commit()
        flash('Pet cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao cadastrar pet: {e}')
        flash('Erro ao cadastrar pet. Confira os dados.', 'error')
        return redirect(url_for('cadastrar_pet'))

    finally:
        if con:
            con.close()


@app.route('/editar_pet/<int:id>', methods=['GET', 'POST'])
def editar_pet(id):
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        if request.method == 'GET':
            cursor.execute("""
                SELECT ID_PET, ID_TUTOR, NOME, ESPECIE, RACA,
                       SEXO, DATA_NASCIMENTO, OBSERVACOES
                FROM PET
                WHERE ID_PET = ?
            """, (id,))

            resultado = cursor.fetchone()

            if not resultado:
                flash('Pet não encontrado.', 'warning')
                return redirect(url_for('dashboard'))

            pet = {
                'id': resultado[0],
                'tutor_id': resultado[1],
                'nome': resultado[2],
                'especie': resultado[3],
                'raca': resultado[4],
                'sexo': resultado[5],
                'data_nascimento': resultado[6].isoformat()
                    if resultado[6] else '',
                'observacoes': resultado[7] or ''
            }

            tutores = listar_tutores_para_pet(cursor)

            return render_template(
                'editarPet.html',
                pet=pet,
                tutores=tutores,
                especies=opcoes_especies
            )

        nome = request.form['nome'].strip()
        tutor_id = int(request.form['tutor'])
        especie = request.form['especie']
        raca = request.form['raca'].strip()
        sexo = request.form['sexo']
        nascimento = date.fromisoformat(request.form['data_nascimento'])
        observacoes = request.form.get('observacoes', '').strip() or None

        if sexo not in ('MACHO', 'FEMEA'):
            flash('Selecione um sexo válido.', 'warning')
            return redirect(url_for('editar_pet', id=id))

        cursor.execute("""
            UPDATE PET
            SET ID_TUTOR = ?, NOME = ?, ESPECIE = ?, RACA = ?,
                SEXO = ?, DATA_NASCIMENTO = ?, OBSERVACOES = ?
            WHERE ID_PET = ?
        """, (
            tutor_id, nome, especie, raca, sexo,
            nascimento, observacoes, id
        ))

        con.commit()
        flash('Pet atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao editar pet: {e}')
        flash('Erro ao editar pet. Confira os dados.', 'error')
        return redirect(url_for('dashboard'))

    finally:
        if con:
            con.close()


@app.route('/remover_pet/<int:id>', methods=['POST'])
def remover_pet(id):
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        cursor.execute("""
            DELETE FROM PET
            WHERE ID_PET = ?
        """, (id,))

        con.commit()
        flash('Pet removido com sucesso!', 'success')

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao remover pet: {e}')
        flash(
            'Não foi possível remover o pet. Verifique se ele possui agendamentos.',
            'warning'
        )

    finally:
        if con:
            con.close()

    return redirect(url_for('dashboard'))

def buscar_pets(cursor):
    cursor.execute("""
        SELECT ID_PET, NOME
        FROM PET
        ORDER BY NOME
    """)
    return [
        {'id': linha[0], 'nome': linha[1]}
        for linha in cursor.fetchall()
    ]


@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None

    try:
        con = conectar()
        cursor = con.cursor()

        pets = buscar_pets(cursor)

        if not pets:
            flash('Cadastre um pet antes de marcar uma consulta.', 'warning')
            return redirect(url_for('dashboard'))

        if request.method == 'GET':
            return render_template(
                'agendar.html',
                pets=pets,
                opcoes=opcoes_atend
            )

        pet_id = int(request.form['pet_agendar'])
        tipo = request.form['tipo'].strip()
        datahora = datetime.fromisoformat(request.form['datahora'])
        descricao = request.form.get('desc', '').strip() or None

        if not tipo:
            flash('Informe o tipo de serviço.', 'warning')
            return redirect(url_for('agendar'))

        if datahora < datetime.now():
            flash('Não é possível agendar em uma data passada.', 'warning')
            return redirect(url_for('agendar'))

        cursor.execute(
            "SELECT ID_PET FROM PET WHERE ID_PET = ?",
            (pet_id,)
        )

        if not cursor.fetchone():
            flash('Pet não encontrado.', 'warning')
            return redirect(url_for('agendar'))

        cursor.execute("""
            INSERT INTO AGENDAMENTO
                (ID_PET, ID_USUARIO, DATA_HORA,
                 TIPO_SERVICO, DESCRICAO, STATUS)
            VALUES (?, ?, ?, ?, ?, 'AGENDADO')
        """, (
            pet_id,
            session['usuario_id'],
            datahora,
            tipo,
            descricao
        ))

        con.commit()

        flash('Consulta agendada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        print("ERRO AO AGENDAR CONSULTA:", repr(e))

        if con:
            con.rollback()

        flash('Erro ao agendar consulta.', 'error')
        return redirect(url_for('dashboard'))

    finally:
        if con:
            con.close()



@app.route('/editar_consulta/<int:id>', methods=['GET', 'POST'])
def editar_consulta(id):
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        cursor.execute("""
            SELECT A.ID_AGENDAMENTO, A.ID_PET, A.DATA_HORA,
                   A.TIPO_SERVICO, A.DESCRICAO, A.STATUS
            FROM AGENDAMENTO A
            WHERE A.ID_AGENDAMENTO = ?
        """, (id,))

        resultado = cursor.fetchone()

        if not resultado or resultado[5] == 'CANCELADO':
            flash('Agendamento não encontrado ou cancelado.', 'warning')
            return redirect(url_for('dashboard'))

        pets = buscar_pets(cursor)

        if request.method == 'GET':
            consulta = {
                'id': resultado[0],
                'pet_agendar': resultado[1],
                'datahora': resultado[2].strftime('%Y-%m-%dT%H:%M'),
                'tipo': resultado[3],
                'desc': resultado[4] or ''
            }

            return render_template(
                'editarConsulta.html',
                consulta=consulta,
                pets=pets,
                opcoes=opcoes_atend
            )

        pet_id = int(request.form['pet_agendar'])
        tipo = request.form['tipo'].strip()
        datahora = datetime.fromisoformat(request.form['datahora'])
        descricao = request.form.get('desc', '').strip() or None

        if datahora < datetime.now():
            flash('Não é possível agendar em uma data passada.', 'warning')
            return redirect(url_for('editar_consulta', id=id))

        cursor.execute(
            "SELECT ID_PET FROM PET WHERE ID_PET = ?",
            (pet_id,)
        )
        if not cursor.fetchone():
            flash('Pet não encontrado.', 'warning')
            return redirect(url_for('editar_consulta', id=id))

        cursor.execute("""
            UPDATE AGENDAMENTO
            SET ID_PET = ?, DATA_HORA = ?,
                TIPO_SERVICO = ?, DESCRICAO = ?
            WHERE ID_AGENDAMENTO = ?
        """, (pet_id, datahora, tipo, descricao, id))

        con.commit()
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao editar agendamento: {e}')
        flash('Erro ao editar agendamento.', 'error')
        return redirect(url_for('dashboard'))

    finally:
        if con:
            con.close()


@app.route('/desmarcar/<int:id>', methods=['POST'])
def desmarcar(id):
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None
    try:
        con = conectar()
        cursor = con.cursor()

        cursor.execute("""
            UPDATE AGENDAMENTO
            SET STATUS = 'CANCELADO'
            WHERE ID_AGENDAMENTO = ?
              AND STATUS <> 'CANCELADO'
        """, (id,))

        con.commit()
        flash('Agendamento cancelado!', 'success')

    except Exception as e:
        if con:
            con.rollback()
        print(f'Erro ao cancelar agendamento: {e}')
        flash('Erro ao cancelar agendamento.', 'error')

    finally:
        if con:
            con.close()

    return redirect(url_for('dashboard'))


# calcular o soro para um pet específico
@app.route('/calcular_dose/<id>', methods=["GET", "POST"])
def calcular_dose(id):
    if request.method == "GET":
        return render_template('calcularDose.html')

    try:
        pet = obter_item(pets, int(id))  # obtendo o pet em questão
        peso = int(pet['peso']) / 1000  # convertendo gramas em quilos

        dose_recomendada = float(request.form['dose'])

        if dose_recomendada <= 0:
            flash('Dose não pode ser menor ou igual a zero', 'warning')
            return redirect(f'/calcular_dose/{id}')

        resultado = peso * dose_recomendada
        flash(f"Dose a ser administrada: {resultado:.2f} mg", 'success')

        pet['dose'] = resultado
    except Exception as e:
        flash('Houve um erro ao realizar o cálculo', 'error')
        return redirect(f'/calcular_dose/{id}')

    return redirect(url_for('dashboard'))

@app.route('/calcular_soro/<id>', methods=["GET", "POST"])
def calcular_soro(id):
    if usuario_atual is None:
        return redirect(url_for('login'))

    if request.method == "GET":
        return render_template('calcularSoro.html', pets=obter_lista_relacionada(pets, 'donoId', usuario_atual['id']))

    try:
        pet = obter_item(pets, int(id)) # obtendo o pet em questão
        desidratacao = float(request.form['desid'])
        peso = int(pet['peso'])/1000 # convertendo gramas em quilos

        resultado = desidratacao * base_fluido * peso

        flash(f"Dose de soro a ser administrada: {resultado:.2f} mL/kg", 'success')

        pet['soro'] = resultado
    except Exception as e:
        flash(f"Erro ao calcular dose: {e}", 'error')

    return redirect(url_for('dashboard'))

# rota dashboard, esse é o painel principal do usuário

@app.route('/dashboard')
def dashboard():
    if not session.get('usuario_id'):
        return redirect(url_for('login'))

    con = None

    try:
        con = conectar()
        cursor = con.cursor()

        # BUSCAR PETS NO FIREBIRD
        cursor.execute("""
            SELECT P.ID_PET, P.ID_TUTOR, P.NOME, P.ESPECIE,
                   P.RACA, P.SEXO, P.DATA_NASCIMENTO,
                   P.OBSERVACOES, T.NOME
            FROM PET P
            INNER JOIN TUTOR T ON T.ID_TUTOR = P.ID_TUTOR
            ORDER BY P.NOME
        """)

        resultados = cursor.fetchall()

        pets = []

        for p in resultados:
            pets.append({
                'id': p[0],
                'tutor_id': p[1],
                'nome': p[2],
                'especie': p[3],
                'raca': p[4],
                'sexo': p[5],
                'data_nascimento': p[6],
                'observacoes': p[7],
                'nome_tutor': p[8]
            })

        # BUSCAR CONSULTAS NO FIREBIRD
        cursor.execute("""
            SELECT A.ID_AGENDAMENTO, A.ID_PET, A.DATA_HORA,
                   A.TIPO_SERVICO, A.DESCRICAO, P.NOME
            FROM AGENDAMENTO A
            INNER JOIN PET P ON P.ID_PET = A.ID_PET
            WHERE A.STATUS <> 'CANCELADO'
            ORDER BY A.DATA_HORA
        """)

        resultados_consultas = cursor.fetchall()

        consultas = []

        for c in resultados_consultas:
            consultas.append({
                'id': c[0],
                'pet_id': c[1],
                'datahora': c[2],
                'tipo': c[3],
                'desc': c[4] or '',
                'nome_pet': c[5]
            })

        # DADOS DO ADMINISTRADOR LOGADO
        usuario = {
            'id': session['usuario_id'],
            'nome': session.get('usuario_nome')
        }

        return render_template(
            'dashboard.html',
            usuario=usuario,
            pets=pets,
            qtd=len(pets),
            consultas=consultas,
            obter=obter_item
        )

    except Exception as e:
        print(f'Erro no dashboard: {e}')
        flash('Erro ao carregar o painel.', 'error')
        return redirect(url_for('login'))

    finally:
        if con:
            con.close()

if __name__ == "__main__":
    app.run(debug=True)