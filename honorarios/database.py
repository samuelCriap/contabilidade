"""
Módulo de banco de dados para o Sistema de Honorários Contábeis.
Utiliza SQLite para armazenamento local.
"""
import sqlite3
import os
from datetime import datetime

import sys

# Caminho do banco de dados
def get_resource_path(relative_path):
    """Retorna o caminho absoluto do recurso, priorizando arquivos locais externos"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        
        # 1. Tentar na pasta "Data" ao lado do executável
        external_data_path = os.path.join(base_path, "Data", relative_path)
        if os.path.exists(external_data_path):
            return external_data_path
            
        # 2. Tentar na raiz do executável (fallback)
        external_root_path = os.path.join(base_path, relative_path)
        if os.path.exists(external_root_path):
            return external_root_path
            
        # 2. Se não achar externo, usa o interno (PyInstaller bundle)
        if hasattr(sys, '_MEIPASS'):
            # O PyInstaller pode achatar a estrutura ou manter.
            return os.path.join(sys._MEIPASS, "honorarios", "data", relative_path)
    
    # Desenvolvimento
    return os.path.join(os.path.abspath("honorarios/data"), relative_path)

if getattr(sys, 'frozen', False):
    # Executável
    # 1. Tentar usar DB local (portabilidade)
    exe_dir = os.path.dirname(sys.executable)
    
    # Prioridade 1: Pasta 'Data' ao lado do executável
    data_db = os.path.join(exe_dir, "Data", "honorarios.db")
    
    # Prioridade 2: Raiz do executável
    root_db = os.path.join(exe_dir, "honorarios.db")
    
    if os.path.exists(data_db):
        DB_PATH = data_db
    elif os.path.exists(root_db):
        DB_PATH = root_db
    else:
        # Prioridade 3: AppData (padrão se não houver portátil)
        app_data = os.path.join(os.environ['LOCALAPPDATA'], 'HonorariosContabeis')
        os.makedirs(app_data, exist_ok=True)
        DB_PATH = os.path.join(app_data, "honorarios.db")
else:
    # Desenvolvimento
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "honorarios", "data", "honorarios.db")


def get_connection():
    """Retorna conexão com o banco de dados"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Cria as tabelas do sistema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            email TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_interno TEXT,
            nome TEXT NOT NULL,
            cnpj TEXT UNIQUE,
            cpf TEXT,
            endereco TEXT,
            telefone TEXT,
            email TEXT,
            data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP,
            ativo INTEGER DEFAULT 1
        )
    """)
    
    # Tabela de honorários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS honorarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            valor REAL NOT NULL,
            data_vencimento TEXT,
            data_pagamento TEXT,
            status TEXT DEFAULT 'PENDENTE',
            observacao TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)
    
    # Tabela de recibos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recibos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER UNIQUE NOT NULL,
            cliente_id INTEGER NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            data_emissao TEXT DEFAULT CURRENT_TIMESTAMP,
            referencia_mes INTEGER,
            referencia_ano INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)
    
    # Tabela de configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    
    # Tabela de valores de honorários por cliente/ano
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS valores_honorarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            ano INTEGER NOT NULL,
            valor REAL NOT NULL,
            UNIQUE(cliente_id, ano),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)
    
    # Tabela de logs de auditoria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            acao TEXT NOT NULL,
            tabela TEXT,
            registro_id INTEGER,
            detalhes TEXT,
            data_hora TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de certificados digitais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            nome_avulso TEXT,
            cpf_cnpj TEXT,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            midia TEXT,
            validade_anos INTEGER NOT NULL,
            data_emissao TEXT NOT NULL,
            data_vencimento TEXT NOT NULL,
            valor REAL NOT NULL,
            status TEXT DEFAULT 'ATIVO',
            pagamento_status TEXT DEFAULT 'PENDENTE',
            observacao TEXT,
            vinculado_honorario INTEGER DEFAULT 0,
            mes_honorario INTEGER,
            ano_honorario INTEGER,
            data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)
    
    # Adicionar campo cargo na tabela usuarios se não existir
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN cargo TEXT DEFAULT 'usuario'")
    except:
        pass
    
    # Adicionar campo nome na tabela usuarios se não existir
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nome TEXT")
    except:
        pass
    
    # Adicionar campo status na tabela usuarios se não existir
    # status: 'ativo', 'pendente', 'bloqueado'
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN status TEXT DEFAULT 'ativo'")
    except:
        pass
    
    # Adicionar campo pagamento_status na tabela certificados se não existir
    try:
        cursor.execute("ALTER TABLE certificados ADD COLUMN pagamento_status TEXT DEFAULT 'PENDENTE'")
    except:
        pass
    
    # Adicionar campo valor_honorario na tabela clientes se não existir
    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN valor_honorario REAL")
    except:
        pass
    
    # Adicionar campo forma_pagamento na tabela honorarios se não existir
    try:
        cursor.execute("ALTER TABLE honorarios ADD COLUMN forma_pagamento TEXT")
    except:
        pass
    
    conn.commit()
    conn.close()


def criar_usuario_inicial():
    """Cria usuário admin padrão se não existir"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha, email, cargo) VALUES (?, ?, ?, ?)",
            ("admin", "admin123", "admin@escritorio.com", "admin")
        )
        conn.commit()
    
    conn.close()


# === FUNÇÕES DE USUÁRIOS ===

def cadastrar_usuario(usuario, senha, nome=None, email=None, cargo='usuario', status='pendente'):
    """Cadastra um novo usuário (status pendente até admin aprovar)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, senha, nome, email, cargo, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario, senha, nome, email, cargo, status))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Usuário já existe


def listar_usuarios():
    """Lista todos os usuários"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario, nome, email, cargo, status, data_criacao FROM usuarios ORDER BY usuario")
    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return usuarios


def buscar_usuario(usuario):
    """Busca usuário por nome de usuário e retorna dados completos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None


def atualizar_cargo_usuario(usuario_id, novo_cargo):
    """Atualiza o cargo de um usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET cargo = ? WHERE id = ?", (novo_cargo, usuario_id))
    conn.commit()
    conn.close()


def excluir_usuario(usuario_id):
    """Exclui um usuário (exceto admin)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario FROM usuarios WHERE id = ?", (usuario_id,))
    user = cursor.fetchone()
    if user and user['usuario'] == 'admin':
        conn.close()
        return False  # Não pode excluir admin
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    return True


def is_admin(usuario):
    """Verifica se usuário é admin"""
    user = buscar_usuario(usuario)
    return user and user.get('cargo') == 'admin'


def aprovar_usuario(usuario_id):
    """Aprova um usuário pendente (muda status para 'ativo')"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET status = 'ativo' WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()


def bloquear_usuario(usuario_id):
    """Bloqueia um usuário (muda status para 'bloqueado')"""
    conn = get_connection()
    cursor = conn.cursor()
    # Não permite bloquear admin principal
    cursor.execute("SELECT usuario FROM usuarios WHERE id = ?", (usuario_id,))
    user = cursor.fetchone()
    if user and user['usuario'] == 'admin':
        conn.close()
        return False
    cursor.execute("UPDATE usuarios SET status = 'bloqueado' WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    return True


def atualizar_status_usuario(usuario_id, novo_status):
    """Atualiza o status de um usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET status = ? WHERE id = ?", (novo_status, usuario_id))
    conn.commit()
    conn.close()

def registrar_log(usuario, acao, tabela=None, registro_id=None, detalhes=None):
    """Registra uma ação no log de auditoria"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs_auditoria (usuario, acao, tabela, registro_id, detalhes)
        VALUES (?, ?, ?, ?, ?)
    """, (usuario, acao, tabela, registro_id, detalhes))
    conn.commit()
    conn.close()


# === FUNÇÕES DE CLIENTES ===

def listar_clientes(ativo=True):
    """Lista todos os clientes"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE ativo = ? ORDER BY nome", (1 if ativo else 0,))
    clientes = cursor.fetchall()
    conn.close()
    return clientes


def adicionar_cliente(nome, cnpj=None, cpf=None, endereco=None, telefone=None, email=None, codigo_interno=None, valor_honorario=None):
    """Adiciona um novo cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes (codigo_interno, nome, cnpj, cpf, endereco, telefone, email, valor_honorario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo_interno, nome, cnpj, cpf, endereco, telefone, email, valor_honorario))
    conn.commit()
    cliente_id = cursor.lastrowid
    conn.close()
    return cliente_id


def atualizar_cliente(cliente_id, nome, cnpj=None, cpf=None, endereco=None, telefone=None, email=None, codigo_interno=None, valor_honorario=None):
    """Atualiza dados de um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clientes 
        SET codigo_interno=?, nome=?, cnpj=?, cpf=?, endereco=?, telefone=?, email=?, valor_honorario=?
        WHERE id=?
    """, (codigo_interno, nome, cnpj, cpf, endereco, telefone, email, valor_honorario, cliente_id))
    conn.commit()
    conn.close()


def buscar_cliente(cliente_id):
    """Busca um cliente pelo ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()
    conn.close()
    return cliente


# === FUNÇÕES DE HONORÁRIOS ===

def listar_honorarios(ano=None, cliente_id=None, status=None):
    """Lista honorários com filtros opcionais"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT h.*, c.nome as cliente_nome 
        FROM honorarios h 
        JOIN clientes c ON h.cliente_id = c.id
        WHERE 1=1
    """
    params = []
    
    if ano:
        query += " AND h.ano = ?"
        params.append(ano)
    
    if cliente_id:
        query += " AND h.cliente_id = ?"
        params.append(cliente_id)
    
    if status:
        query += " AND h.status = ?"
        params.append(status)
    
    query += " ORDER BY h.ano DESC, h.mes DESC, c.nome"
    
    cursor.execute(query, params)
    honorarios = cursor.fetchall()
    conn.close()
    return honorarios


def adicionar_honorario(cliente_id, ano, mes, valor, data_vencimento=None, observacao=None):
    """Adiciona um novo honorário"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO honorarios (cliente_id, ano, mes, valor, data_vencimento, observacao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cliente_id, ano, mes, valor, data_vencimento, observacao))
    conn.commit()
    conn.close()


def atualizar_honorario(honorario_id, status=None, data_pagamento=None, observacao=None):
    """Atualiza um honorário"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("UPDATE honorarios SET status = ? WHERE id = ?", (status, honorario_id))
    if data_pagamento:
        cursor.execute("UPDATE honorarios SET data_pagamento = ? WHERE id = ?", (data_pagamento, honorario_id))
    if observacao is not None:
        cursor.execute("UPDATE honorarios SET observacao = ? WHERE id = ?", (observacao, honorario_id))
    
    conn.commit()
    conn.close()


def marcar_como_pago(honorario_id, forma_pagamento=None, data_pagamento=None):
    """Marca um honorário como pago com forma de pagamento e data opcional"""
    if data_pagamento is None:
        data_pagamento = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE honorarios SET status = 'PAGO', data_pagamento = ?, forma_pagamento = ? WHERE id = ?",
        (data_pagamento, forma_pagamento, honorario_id)
    )
    conn.commit()
    conn.close()


def get_resumo_ano(ano):
    """Retorna resumo de honorários do ano"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'PAGO' THEN 1 ELSE 0 END) as pagos,
            SUM(CASE WHEN status = 'PENDENTE' THEN 1 ELSE 0 END) as pendentes,
            SUM(CASE WHEN status = 'ATRASADO' THEN 1 ELSE 0 END) as atrasados,
            SUM(valor) as valor_total,
            SUM(CASE WHEN status = 'PAGO' THEN valor ELSE 0 END) as valor_recebido,
            SUM(CASE WHEN status != 'PAGO' THEN valor ELSE 0 END) as valor_pendente
        FROM honorarios
        WHERE ano = ?
    """, (ano,))
    
    resumo = cursor.fetchone()
    conn.close()
    return resumo


# === FUNÇÕES DE RECIBOS ===

def gerar_proximo_numero_recibo():
    """Gera o próximo número de recibo"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(numero) FROM recibos")
    result = cursor.fetchone()[0]
    conn.close()
    return (result or 0) + 1


def criar_recibo(cliente_id, valor, descricao, referencia_mes=None, referencia_ano=None):
    """Cria um novo recibo"""
    numero = gerar_proximo_numero_recibo()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recibos (numero, cliente_id, valor, descricao, referencia_mes, referencia_ano)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (numero, cliente_id, valor, descricao, referencia_mes, referencia_ano))
    conn.commit()
    recibo_id = cursor.lastrowid
    conn.close()
    return recibo_id, numero


def listar_recibos(cliente_id=None, ano=None):
    """Lista recibos com filtros"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT r.*, c.nome as cliente_nome 
        FROM recibos r 
        JOIN clientes c ON r.cliente_id = c.id
        WHERE 1=1
    """
    params = []
    
    if cliente_id:
        query += " AND r.cliente_id = ?"
        params.append(cliente_id)
    
    if ano:
        query += " AND r.referencia_ano = ?"
        params.append(ano)
    
    query += " ORDER BY r.data_emissao DESC"
    
    cursor.execute(query, params)
    recibos = cursor.fetchall()
    conn.close()
    return recibos


def buscar_recibo(recibo_id):
    """Busca um recibo pelo ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, c.nome as cliente_nome, c.cnpj, c.cpf, c.endereco
        FROM recibos r 
        JOIN clientes c ON r.cliente_id = c.id
        WHERE r.id = ?
    """, (recibo_id,))
    recibo = cursor.fetchone()
    conn.close()
    return recibo


# === FUNÇÕES DE CONFIGURAÇÕES ===

def get_config(chave, padrao=None):
    """Obtém uma configuração"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else padrao


def set_config(chave, valor):
    """Define uma configuração"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)
    """, (chave, valor))
    conn.commit()
    conn.close()


# === FUNÇÕES DE VALORES DE HONORÁRIOS POR ANO ===

def get_valor_honorario_ano(cliente_id, ano):
    """Obtém valor de honorário do cliente para um ano específico"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT valor FROM valores_honorarios WHERE cliente_id = ? AND ano = ?",
        (cliente_id, ano)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def set_valor_honorario_ano(cliente_id, ano, valor):
    """Define valor de honorário do cliente para um ano específico"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO valores_honorarios (cliente_id, ano, valor)
        VALUES (?, ?, ?)
    """, (cliente_id, ano, valor))
    conn.commit()
    conn.close()


def listar_valores_honorarios_cliente(cliente_id):
    """Lista todos os valores de honorários por ano de um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ano, valor FROM valores_honorarios WHERE cliente_id = ? ORDER BY ano",
        (cliente_id,)
    )
    valores = cursor.fetchall()
    conn.close()
    return valores


def adicionar_cliente_com_valor(nome, cnpj=None, cpf=None, endereco=None, telefone=None, email=None, valor_2025=None, codigo_interno=None):
    """Adiciona um novo cliente e opcionalmente cria honorários para 2025"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Inserir cliente
    cursor.execute("""
        INSERT INTO clientes (codigo_interno, nome, cnpj, cpf, endereco, telefone, email)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (codigo_interno, nome, cnpj, cpf, endereco, telefone, email))
    
    cliente_id = cursor.lastrowid
    
    # Se tem valor, salvar valor do ano e criar honorários de 2025
    if valor_2025 and valor_2025 > 0:
        # Salvar valor padrão para 2025
        cursor.execute("""
            INSERT OR REPLACE INTO valores_honorarios (cliente_id, ano, valor)
            VALUES (?, 2025, ?)
        """, (cliente_id, valor_2025))
        
        # Criar honorários para cada mês de 2025 (incluindo 13º = mês 13)
        for mes in range(1, 14):
            cursor.execute("""
                INSERT OR IGNORE INTO honorarios (cliente_id, ano, mes, valor, status)
                VALUES (?, 2025, ?, ?, 'PENDENTE')
            """, (cliente_id, mes, valor_2025))
    
    conn.commit()
    conn.close()
    return cliente_id


def criar_honorarios_ano_cliente(cliente_id, ano, valor):
    """Cria honorários para todos os meses de um ano para um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Salvar valor padrão do ano
    cursor.execute("""
        INSERT OR REPLACE INTO valores_honorarios (cliente_id, ano, valor)
        VALUES (?, ?, ?)
    """, (cliente_id, ano, valor))
    
    # Criar honorários para cada mês
    for mes in range(1, 13):
        # Verificar se já existe
        cursor.execute("""
            SELECT id FROM honorarios WHERE cliente_id = ? AND ano = ? AND mes = ?
        """, (cliente_id, ano, mes))
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO honorarios (cliente_id, ano, mes, valor, status)
                VALUES (?, ?, ?, ?, 'PENDENTE')
            """, (cliente_id, ano, mes, valor))
    
    conn.commit()
    conn.close()


def gerar_honorarios_mes_atual():
    """
    Gera automaticamente honorários PENDENTES para o mês atual
    para todos os clientes ativos que têm valor cadastrado para o ano.
    Retorna quantidade de honorários criados.
    """
    from datetime import datetime
    
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar todos os clientes ativos
    cursor.execute("SELECT id, nome FROM clientes WHERE ativo = 1")
    clientes = cursor.fetchall()
    
    criados = 0
    
    for cliente in clientes:
        cliente_id = cliente['id']
        
        # Verificar se já existe honorário para este mês/ano
        cursor.execute("""
            SELECT id FROM honorarios 
            WHERE cliente_id = ? AND ano = ? AND mes = ?
        """, (cliente_id, ano_atual, mes_atual))
        
        if cursor.fetchone():
            continue  # Já existe
        
        # Buscar valor do ano para o cliente
        cursor.execute("""
            SELECT valor FROM valores_honorarios 
            WHERE cliente_id = ? AND ano = ?
        """, (cliente_id, ano_atual))
        resultado = cursor.fetchone()
        
        if not resultado:
            # Tentar pegar valor do cliente (campo legado)
            cursor.execute("SELECT valor_honorario FROM clientes WHERE id = ?", (cliente_id,))
            valor_result = cursor.fetchone()
            valor = valor_result['valor_honorario'] if valor_result and valor_result['valor_honorario'] else None
        else:
            valor = resultado['valor']
        
        if valor and valor > 0:
            cursor.execute("""
                INSERT INTO honorarios (cliente_id, ano, mes, valor, status)
                VALUES (?, ?, ?, ?, 'PENDENTE')
            """, (cliente_id, ano_atual, mes_atual, valor))
            criados += 1
    
    conn.commit()
    conn.close()
    
    return criados


def recibo_existe(cliente_id, mes, ano):
    """Verifica se já existe recibo para cliente/mês/ano"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM recibos 
        WHERE cliente_id = ? AND referencia_mes = ? AND referencia_ano = ?
    """, (cliente_id, mes, ano))
    result = cursor.fetchone()
    conn.close()
    conn.close()
    return result is not None


def get_relatorio_formas_pagamento(ano):
    """Retorna totais por forma de pagamento no ano"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            CASE 
                WHEN forma_pagamento IS NULL OR forma_pagamento = '' THEN 'Não informado' 
                ELSE forma_pagamento 
            END as metodo,
            COUNT(*) as qtd,
            SUM(valor) as total
        FROM honorarios 
        WHERE ano = ? AND status = 'PAGO'
        GROUP BY 
            CASE 
                WHEN forma_pagamento IS NULL OR forma_pagamento = '' THEN 'Não informado' 
                ELSE forma_pagamento 
            END
        ORDER BY total DESC
    """, (ano,))
    
    dados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return dados



# === FUNÇÕES DE LOG DE AUDITORIA ===

def registrar_log(usuario, acao, tabela=None, registro_id=None, detalhes=None):
    """Registra uma ação no log de auditoria"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs_auditoria (usuario, acao, tabela, registro_id, detalhes)
        VALUES (?, ?, ?, ?, ?)
    """, (usuario, acao, tabela, registro_id, detalhes))
    conn.commit()
    conn.close()


def listar_logs(limite=100, usuario=None, tabela=None):
    """Lista logs de auditoria com filtros"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM logs_auditoria WHERE 1=1"
    params = []
    
    if usuario:
        query += " AND usuario = ?"
        params.append(usuario)
    
    if tabela:
        query += " AND tabela = ?"
        params.append(tabela)
    
    query += " ORDER BY data_hora DESC LIMIT ?"
    params.append(limite)
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    return logs


# === FUNÇÕES DE RELATÓRIO INDIVIDUAL ===

def get_relatorio_cliente(cliente_id):
    """Retorna relatório completo de um cliente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Dados do cliente
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()
    
    if not cliente:
        conn.close()
        return None
    
    # Honorários do cliente
    cursor.execute("""
        SELECT * FROM honorarios 
        WHERE cliente_id = ? 
        ORDER BY ano DESC, mes DESC
    """, (cliente_id,))
    honorarios = cursor.fetchall()
    
    # Resumo por ano
    cursor.execute("""
        SELECT 
            ano,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'PAGO' THEN 1 ELSE 0 END) as pagos,
            SUM(CASE WHEN status != 'PAGO' THEN 1 ELSE 0 END) as pendentes,
            SUM(valor) as valor_total,
            SUM(CASE WHEN status = 'PAGO' THEN valor ELSE 0 END) as valor_pago,
            SUM(CASE WHEN status != 'PAGO' THEN valor ELSE 0 END) as valor_pendente
        FROM honorarios
        WHERE cliente_id = ?
        GROUP BY ano
        ORDER BY ano DESC
    """, (cliente_id,))
    resumo_anos = cursor.fetchall()
    
    # Recibos do cliente
    cursor.execute("""
        SELECT * FROM recibos 
        WHERE cliente_id = ? 
        ORDER BY data_emissao DESC
    """, (cliente_id,))
    recibos = cursor.fetchall()
    
    # Totais gerais
    cursor.execute("""
        SELECT 
            SUM(valor) as total_geral,
            SUM(CASE WHEN status = 'PAGO' THEN valor ELSE 0 END) as total_pago,
            SUM(CASE WHEN status != 'PAGO' THEN valor ELSE 0 END) as saldo_devedor
        FROM honorarios
        WHERE cliente_id = ?
    """, (cliente_id,))
    totais = cursor.fetchone()
    
    conn.close()
    
    return {
        'cliente': dict(cliente) if cliente else None,
        'honorarios': [dict(h) for h in honorarios],
        'resumo_anos': [dict(r) for r in resumo_anos],
        'recibos': [dict(r) for r in recibos],
        'total_geral': totais['total_geral'] or 0,
        'total_pago': totais['total_pago'] or 0,
        'saldo_devedor': totais['saldo_devedor'] or 0,
    }


def get_honorarios_vencendo(dias=7):
    """Retorna honorários que vencem nos próximos X dias"""
    from datetime import datetime, timedelta
    
    conn = get_connection()
    cursor = conn.cursor()
    
    hoje = datetime.now()
    limite = hoje + timedelta(days=dias)
    
    # Busca honorários pendentes do mês atual ou próximo
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    cursor.execute("""
        SELECT h.*, c.nome as cliente_nome, c.email as cliente_email
        FROM honorarios h
        JOIN clientes c ON h.cliente_id = c.id
        WHERE h.status != 'PAGO'
        AND ((h.ano = ? AND h.mes = ?) OR (h.ano = ? AND h.mes = ?))
        ORDER BY h.ano, h.mes, c.nome
    """, (ano_atual, mes_atual, ano_atual, mes_atual + 1 if mes_atual < 12 else 1))
    
    honorarios = cursor.fetchall()
    conn.close()
    
    return [dict(h) for h in honorarios]


def verificar_permissao(usuario, acao):
    """Verifica se usuário tem permissão para ação"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cargo FROM usuarios WHERE usuario = ?", (usuario,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
    
    cargo = result['cargo'] or 'usuario'
    
    # Admin pode tudo
    if cargo == 'admin':
        return True
    
    # Usuário comum não pode deletar ou alterar permissões
    acoes_restritas = ['deletar', 'alterar_permissao', 'gerenciar_usuarios']
    if acao in acoes_restritas:
        return False
    
    return True


def atualizar_cargo_usuario(usuario_id, novo_cargo):
    """Atualiza o cargo de um usuário"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET cargo = ? WHERE id = ?", (novo_cargo, usuario_id))
    conn.commit()
    conn.close()


# Inicializa banco ao importar
create_tables()
criar_usuario_inicial()

# Atualiza admin existente para cargo admin
try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET cargo = 'admin' WHERE usuario = 'admin'")
    conn.commit()
    conn.close()
except:
    pass


# === FUNÇÕES DE CERTIFICADOS DIGITAIS ===

def adicionar_certificado(cliente_id, nome_avulso, cpf_cnpj, tipo, categoria, midia, 
                          validade_anos, data_emissao, data_vencimento, valor, 
                          observacao=None, vinculado_honorario=False, mes_honorario=None, ano_honorario=None):
    """Adiciona um novo certificado digital"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO certificados (cliente_id, nome_avulso, cpf_cnpj, tipo, categoria, midia,
                                  validade_anos, data_emissao, data_vencimento, valor, 
                                  observacao, vinculado_honorario, mes_honorario, ano_honorario)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cliente_id, nome_avulso, cpf_cnpj, tipo, categoria, midia, 
          validade_anos, data_emissao, data_vencimento, valor, 
          observacao, 1 if vinculado_honorario else 0, mes_honorario, ano_honorario))
    conn.commit()
    cert_id = cursor.lastrowid
    conn.close()
    return cert_id


def listar_certificados(status=None, cliente_id=None):
    """Lista certificados com filtros opcionais"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT c.*, cl.nome as cliente_nome 
        FROM certificados c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND c.status = ?"
        params.append(status)
    
    if cliente_id:
        query += " AND c.cliente_id = ?"
        params.append(cliente_id)
    
    query += " ORDER BY c.data_vencimento DESC"
    
    cursor.execute(query, params)
    certificados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return certificados


def buscar_certificado(cert_id):
    """Busca um certificado pelo ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, cl.nome as cliente_nome 
        FROM certificados c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.id = ?
    """, (cert_id,))
    cert = cursor.fetchone()
    conn.close()
    return dict(cert) if cert else None


def atualizar_certificado(cert_id, **kwargs):
    """Atualiza campos de um certificado"""
    conn = get_connection()
    cursor = conn.cursor()
    
    campos = []
    valores = []
    for campo, valor in kwargs.items():
        campos.append(f"{campo} = ?")
        valores.append(valor)
    
    valores.append(cert_id)
    query = f"UPDATE certificados SET {', '.join(campos)} WHERE id = ?"
    cursor.execute(query, valores)
    conn.commit()
    conn.close()


def excluir_certificado(cert_id):
    """Exclui um certificado"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM certificados WHERE id = ?", (cert_id,))
    conn.commit()
    conn.close()


def get_certificados_vencendo(dias=30):
    """Retorna certificados que vencem nos próximos X dias (não inclui já vencidos)"""
    from datetime import datetime, timedelta
    hoje = datetime.now().strftime("%Y-%m-%d")
    data_limite = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, cl.nome as cliente_nome 
        FROM certificados c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.status = 'ATIVO' AND c.data_vencimento >= ? AND c.data_vencimento <= ?
        ORDER BY c.data_vencimento
    """, (hoje, data_limite))
    certs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return certs
