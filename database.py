import sqlite3
from pathlib import Path


DB_PATH = Path("instance") / "banco.db"
ACCOUNT_COLOR_DEFAULT = "#10B981"
CARD_COLOR_DEFAULT = "#0F7A53"
VALID_INVOICE_STATUSES = ("aberta", "fechada", "paga", "vencida")

DEFAULT_CATEGORIES = [
    "Alimentacao",
    "Assinaturas",
    "Casa",
    "Compras",
    "Educacao",
    "Impostos",
    "Investimentos",
    "Lazer",
    "Mercado",
    "Moradia",
    "Saude",
    "Salario",
    "Servicos",
    "Transporte",
    "Viagem",
]


BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    foto TEXT,
    foto_perfil TEXT,
    meta_mensal REAL DEFAULT 0,
    tentativas_falhas INTEGER DEFAULT 0,
    bloqueado_ate DATETIME,
    google_id TEXT
);

CREATE TABLE IF NOT EXISTS tokens_recuperacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    token TEXT NOT NULL,
    expira_em DATETIME NOT NULL,
    usado INTEGER DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    usado_em DATETIME,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    parent_id INTEGER,
    cor TEXT,
    FOREIGN KEY(parent_id) REFERENCES categorias(id)
);

CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    saldo_inicial REAL DEFAULT 0,
    usuario_id INTEGER,
    tipo TEXT DEFAULT 'corrente',
    instituicao TEXT,
    cor TEXT DEFAULT '#10B981',
    ativo INTEGER DEFAULT 1,
    criado_em DATETIME,
    atualizado_em DATETIME,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cartoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    bandeira TEXT,
    limite REAL DEFAULT 0,
    fechamento_dia INTEGER,
    vencimento_dia INTEGER,
    cor TEXT DEFAULT '#0F7A53',
    conta_pagamento_id INTEGER,
    ativo INTEGER DEFAULT 1,
    usuario_id INTEGER,
    criado_em DATETIME,
    atualizado_em DATETIME,
    tipo_cartao TEXT DEFAULT 'credito',
    FOREIGN KEY(conta_pagamento_id) REFERENCES contas(id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    tipo TEXT NOT NULL,
    data DATE,
    categoria_id INTEGER,
    conta_id INTEGER,
    cartao_id INTEGER,
    forma_pagamento TEXT,
    usuario_id INTEGER,
    criado_em DATETIME,
    atualizado_em DATETIME,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id),
    FOREIGN KEY(conta_id) REFERENCES contas(id),
    FOREIGN KEY(cartao_id) REFERENCES cartoes(id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    valor_meta REAL,
    usuario_id INTEGER,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS limites_mensais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    valor_limite REAL NOT NULL,
    criado_em DATETIME,
    atualizado_em DATETIME,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conquistas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    valor_total REAL NOT NULL,
    valor_guardado REAL DEFAULT 0,
    prazo_meses INTEGER,
    criado_em DATETIME,
    atualizado_em DATETIME,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS faturas_cartao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cartao_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    ano INTEGER NOT NULL,
    valor_total REAL DEFAULT 0,
    status TEXT DEFAULT 'aberta' CHECK (status IN ('aberta', 'fechada', 'paga', 'vencida')),
    vencimento DATE,
    fechamento DATE,
    criado_em DATETIME,
    atualizado_em DATETIME,
    FOREIGN KEY(cartao_id) REFERENCES cartoes(id) ON DELETE CASCADE,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transferencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    conta_origem_id INTEGER NOT NULL,
    conta_destino_id INTEGER NOT NULL,
    valor REAL NOT NULL CHECK (valor > 0),
    data DATE NOT NULL,
    descricao TEXT,
    criado_em DATETIME,
    atualizado_em DATETIME,
    CHECK (conta_origem_id <> conta_destino_id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY(conta_origem_id) REFERENCES contas(id) ON DELETE CASCADE,
    FOREIGN KEY(conta_destino_id) REFERENCES contas(id) ON DELETE CASCADE
);
"""


SCHEMA_UPGRADES = [
    ("usuarios", "foto", "TEXT"),
    ("usuarios", "foto_perfil", "TEXT"),
    ("usuarios", "meta_mensal", "REAL DEFAULT 0"),
    ("usuarios", "tentativas_falhas", "INTEGER DEFAULT 0"),
    ("usuarios", "bloqueado_ate", "DATETIME"),
    ("usuarios", "google_id", "TEXT"),
    ("tokens_recuperacao", "usado", "INTEGER DEFAULT 0"),
    ("tokens_recuperacao", "criado_em", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ("tokens_recuperacao", "usado_em", "DATETIME"),
    ("categorias", "parent_id", "INTEGER"),
    ("categorias", "cor", "TEXT"),
    ("contas", "tipo", "TEXT DEFAULT 'corrente'"),
    ("contas", "instituicao", "TEXT"),
    ("contas", "saldo_inicial", "REAL DEFAULT 0"),
    ("contas", "cor", f"TEXT DEFAULT '{ACCOUNT_COLOR_DEFAULT}'"),
    ("contas", "ativo", "INTEGER DEFAULT 1"),
    ("contas", "criado_em", "DATETIME"),
    ("contas", "atualizado_em", "DATETIME"),
    ("cartoes", "bandeira", "TEXT"),
    ("cartoes", "tipo_cartao", "TEXT DEFAULT 'credito'"),
    ("cartoes", "limite", "REAL DEFAULT 0"),
    ("cartoes", "fechamento_dia", "INTEGER"),
    ("cartoes", "vencimento_dia", "INTEGER"),
    ("cartoes", "cor", f"TEXT DEFAULT '{CARD_COLOR_DEFAULT}'"),
    ("cartoes", "conta_pagamento_id", "INTEGER"),
    ("cartoes", "ativo", "INTEGER DEFAULT 1"),
    ("cartoes", "criado_em", "DATETIME"),
    ("cartoes", "atualizado_em", "DATETIME"),
    ("lancamentos", "conta_id", "INTEGER"),
    ("lancamentos", "cartao_id", "INTEGER"),
    ("lancamentos", "forma_pagamento", "TEXT"),
    ("lancamentos", "criado_em", "DATETIME"),
    ("lancamentos", "atualizado_em", "DATETIME"),
    ("limites_mensais", "criado_em", "DATETIME"),
    ("limites_mensais", "atualizado_em", "DATETIME"),
    ("conquistas", "valor_guardado", "REAL DEFAULT 0"),
    ("conquistas", "prazo_meses", "INTEGER"),
    ("conquistas", "criado_em", "DATETIME"),
    ("conquistas", "atualizado_em", "DATETIME"),
    ("faturas_cartao", "criado_em", "DATETIME"),
    ("faturas_cartao", "atualizado_em", "DATETIME"),
    ("transferencias", "criado_em", "DATETIME"),
    ("transferencias", "atualizado_em", "DATETIME"),
]


AUDITED_TABLES = (
    "contas",
    "cartoes",
    "lancamentos",
    "faturas_cartao",
    "transferencias",
    "limites_mensais",
    "conquistas",
)


def conectar():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _table_exists(cursor, table_name):
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _column_info(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1]: row for row in cursor.fetchall()}


def _ensure_column(cursor, table_name, column_name, definition):
    if _table_exists(cursor, table_name) and column_name not in _table_columns(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _foreign_keys(cursor, table_name):
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return [
        {
            "table": row[2],
            "from": row[3],
            "to": row[4],
            "on_delete": row[6],
        }
        for row in cursor.fetchall()
    ]


def _has_fk(cursor, table_name, column_name, ref_table, ref_column="id", on_delete=None):
    for fk in _foreign_keys(cursor, table_name):
        if fk["from"] == column_name and fk["table"] == ref_table and fk["to"] == ref_column:
            if on_delete is None or (fk["on_delete"] or "").upper() == on_delete.upper():
                return True
    return False


def _table_sql(cursor, table_name):
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    row = cursor.fetchone()
    return row[0] if row and row[0] else ""


def _has_not_null(cursor, table_name, column_name):
    info = _column_info(cursor, table_name).get(column_name)
    return bool(info and info[3])


def _column_type(cursor, table_name, column_name):
    info = _column_info(cursor, table_name).get(column_name)
    return (info[2] if info else "").upper()


def _prepare_rebuild(cursor, table_name):
    cursor.execute(f"DROP TABLE IF EXISTS temp.__backup_{table_name}")
    cursor.execute(f"CREATE TEMP TABLE __backup_{table_name} AS SELECT * FROM {table_name}")
    cursor.execute(f"SELECT COUNT(*) FROM temp.__backup_{table_name}")
    return cursor.fetchone()[0]


def _validate_copy_count(cursor, table_name, expected_count):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    copied_count = cursor.fetchone()[0]
    if copied_count != expected_count:
        raise RuntimeError(
            f"Migracao de {table_name} interrompida: {copied_count} de {expected_count} registros copiados."
        )


def _rebuild_categorias_if_needed(cursor):
    if not _table_exists(cursor, "categorias"):
        return False

    needs_rebuild = any(
        [
            not _has_fk(cursor, "categorias", "parent_id", "categorias"),
            _column_type(cursor, "categorias", "cor") not in {"", "TEXT"},
        ]
    )
    if not needs_rebuild:
        return False

    expected_count = _prepare_rebuild(cursor, "categorias")
    has_lancamentos = _table_exists(cursor, "lancamentos")
    expected_lancamentos = _prepare_rebuild(cursor, "lancamentos") if has_lancamentos else 0

    if has_lancamentos:
        cursor.execute("DROP TABLE lancamentos")
    cursor.execute("DROP TABLE categorias")
    cursor.execute(
        """
        CREATE TABLE categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            parent_id INTEGER,
            cor TEXT,
            FOREIGN KEY(parent_id) REFERENCES categorias(id)
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO categorias (id, nome, parent_id, cor)
        SELECT
            id,
            nome,
            CASE
                WHEN parent_id IS NOT NULL
                 AND EXISTS (SELECT 1 FROM temp.__backup_categorias p WHERE p.id = temp.__backup_categorias.parent_id)
                THEN parent_id
                ELSE NULL
            END,
            cor
        FROM temp.__backup_categorias
        """
    )
    _validate_copy_count(cursor, "categorias", expected_count)

    if has_lancamentos:
        cursor.execute(
            """
            CREATE TABLE lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                tipo TEXT NOT NULL,
                data DATE,
                categoria_id INTEGER,
                conta_id INTEGER,
                cartao_id INTEGER,
                forma_pagamento TEXT,
                usuario_id INTEGER,
                criado_em DATETIME,
                atualizado_em DATETIME,
                FOREIGN KEY(categoria_id) REFERENCES categorias(id),
                FOREIGN KEY(conta_id) REFERENCES contas(id),
                FOREIGN KEY(cartao_id) REFERENCES cartoes(id),
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO lancamentos (
                id, descricao, valor, tipo, data, categoria_id, conta_id, cartao_id,
                forma_pagamento, usuario_id, criado_em, atualizado_em
            )
            SELECT
                id,
                descricao,
                valor,
                tipo,
                data,
                CASE
                    WHEN categoria_id IS NOT NULL
                     AND EXISTS (SELECT 1 FROM categorias c WHERE c.id = temp.__backup_lancamentos.categoria_id)
                    THEN categoria_id
                    ELSE NULL
                END,
                CASE
                    WHEN conta_id IS NOT NULL
                     AND EXISTS (SELECT 1 FROM contas c WHERE c.id = temp.__backup_lancamentos.conta_id)
                    THEN conta_id
                    ELSE NULL
                END,
                CASE
                    WHEN cartao_id IS NOT NULL
                     AND EXISTS (SELECT 1 FROM cartoes c WHERE c.id = temp.__backup_lancamentos.cartao_id)
                    THEN cartao_id
                    ELSE NULL
                END,
                forma_pagamento,
                CASE
                    WHEN usuario_id IS NOT NULL
                     AND EXISTS (SELECT 1 FROM usuarios u WHERE u.id = temp.__backup_lancamentos.usuario_id)
                    THEN usuario_id
                    ELSE NULL
                END,
                COALESCE(criado_em, CURRENT_TIMESTAMP),
                COALESCE(atualizado_em, CURRENT_TIMESTAMP)
            FROM temp.__backup_lancamentos
            """
        )
        _validate_copy_count(cursor, "lancamentos", expected_lancamentos)

    return True


def _rebuild_lancamentos_if_needed(cursor):
    if not _table_exists(cursor, "lancamentos"):
        return False

    needs_rebuild = any(
        [
            not _has_fk(cursor, "lancamentos", "categoria_id", "categorias"),
            not _has_fk(cursor, "lancamentos", "conta_id", "contas"),
            not _has_fk(cursor, "lancamentos", "cartao_id", "cartoes"),
            not _has_fk(cursor, "lancamentos", "usuario_id", "usuarios", on_delete="CASCADE"),
        ]
    )
    if not needs_rebuild:
        return False

    expected_count = _prepare_rebuild(cursor, "lancamentos")
    cursor.execute("DROP TABLE lancamentos")
    cursor.execute(
        """
        CREATE TABLE lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL,
            data DATE,
            categoria_id INTEGER,
            conta_id INTEGER,
            cartao_id INTEGER,
            forma_pagamento TEXT,
            usuario_id INTEGER,
            criado_em DATETIME,
            atualizado_em DATETIME,
            FOREIGN KEY(categoria_id) REFERENCES categorias(id),
            FOREIGN KEY(conta_id) REFERENCES contas(id),
            FOREIGN KEY(cartao_id) REFERENCES cartoes(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO lancamentos (
            id, descricao, valor, tipo, data, categoria_id, conta_id, cartao_id,
            forma_pagamento, usuario_id, criado_em, atualizado_em
        )
        SELECT
            id,
            descricao,
            valor,
            tipo,
            data,
            CASE
                WHEN categoria_id IS NOT NULL
                 AND EXISTS (SELECT 1 FROM categorias c WHERE c.id = temp.__backup_lancamentos.categoria_id)
                THEN categoria_id
                ELSE NULL
            END,
            CASE
                WHEN conta_id IS NOT NULL
                 AND EXISTS (SELECT 1 FROM contas c WHERE c.id = temp.__backup_lancamentos.conta_id)
                THEN conta_id
                ELSE NULL
            END,
            CASE
                WHEN cartao_id IS NOT NULL
                 AND EXISTS (SELECT 1 FROM cartoes c WHERE c.id = temp.__backup_lancamentos.cartao_id)
                THEN cartao_id
                ELSE NULL
            END,
            forma_pagamento,
            CASE
                WHEN usuario_id IS NOT NULL
                 AND EXISTS (SELECT 1 FROM usuarios u WHERE u.id = temp.__backup_lancamentos.usuario_id)
                THEN usuario_id
                ELSE NULL
            END,
            COALESCE(criado_em, CURRENT_TIMESTAMP),
            COALESCE(atualizado_em, CURRENT_TIMESTAMP)
        FROM temp.__backup_lancamentos
        """
    )
    _validate_copy_count(cursor, "lancamentos", expected_count)
    return True


def _validate_transferencias_for_rebuild(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM temp.__backup_transferencias t
        WHERE valor <= 0
           OR conta_origem_id = conta_destino_id
           OR usuario_id IS NULL
           OR conta_origem_id IS NULL
           OR conta_destino_id IS NULL
           OR NOT EXISTS (SELECT 1 FROM usuarios u WHERE u.id = t.usuario_id)
           OR NOT EXISTS (SELECT 1 FROM contas c WHERE c.id = t.conta_origem_id)
           OR NOT EXISTS (SELECT 1 FROM contas c WHERE c.id = t.conta_destino_id)
        """
    )
    invalid_count = cursor.fetchone()[0]
    if invalid_count:
        raise RuntimeError(
            f"Migracao de transferencias interrompida: {invalid_count} registro(s) violam as novas constraints."
        )


def _rebuild_transferencias_if_needed(cursor):
    if not _table_exists(cursor, "transferencias"):
        return False

    sql = _table_sql(cursor, "transferencias").upper()
    needs_rebuild = any(
        [
            not _has_fk(cursor, "transferencias", "usuario_id", "usuarios", on_delete="CASCADE"),
            not _has_fk(cursor, "transferencias", "conta_origem_id", "contas", on_delete="CASCADE"),
            not _has_fk(cursor, "transferencias", "conta_destino_id", "contas", on_delete="CASCADE"),
            "CHECK (VALOR > 0)" not in sql and "CHECK(VALOR > 0)" not in sql,
            "CONTA_ORIGEM_ID <> CONTA_DESTINO_ID" not in sql,
        ]
    )
    if not needs_rebuild:
        return False

    expected_count = _prepare_rebuild(cursor, "transferencias")
    _validate_transferencias_for_rebuild(cursor)
    cursor.execute("DROP TABLE transferencias")
    cursor.execute(
        """
        CREATE TABLE transferencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            conta_origem_id INTEGER NOT NULL,
            conta_destino_id INTEGER NOT NULL,
            valor REAL NOT NULL CHECK (valor > 0),
            data DATE NOT NULL,
            descricao TEXT,
            criado_em DATETIME,
            atualizado_em DATETIME,
            CHECK (conta_origem_id <> conta_destino_id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY(conta_origem_id) REFERENCES contas(id) ON DELETE CASCADE,
            FOREIGN KEY(conta_destino_id) REFERENCES contas(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO transferencias (
            id, usuario_id, conta_origem_id, conta_destino_id, valor, data,
            descricao, criado_em, atualizado_em
        )
        SELECT
            id, usuario_id, conta_origem_id, conta_destino_id, valor, data,
            descricao, COALESCE(criado_em, CURRENT_TIMESTAMP), COALESCE(atualizado_em, CURRENT_TIMESTAMP)
        FROM temp.__backup_transferencias
        """
    )
    _validate_copy_count(cursor, "transferencias", expected_count)
    return True


def _validate_faturas_for_rebuild(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM temp.__backup_faturas_cartao f
        WHERE cartao_id IS NULL
           OR usuario_id IS NULL
           OR mes IS NULL
           OR ano IS NULL
           OR mes NOT BETWEEN 1 AND 12
           OR (status IS NOT NULL AND status NOT IN ('aberta', 'fechada', 'paga', 'vencida'))
           OR NOT EXISTS (SELECT 1 FROM usuarios u WHERE u.id = f.usuario_id)
           OR NOT EXISTS (SELECT 1 FROM cartoes c WHERE c.id = f.cartao_id)
        """
    )
    invalid_count = cursor.fetchone()[0]
    if invalid_count:
        raise RuntimeError(
            f"Migracao de faturas_cartao interrompida: {invalid_count} registro(s) violam as novas constraints."
        )


def _rebuild_faturas_if_needed(cursor):
    if not _table_exists(cursor, "faturas_cartao"):
        return False

    sql = _table_sql(cursor, "faturas_cartao").upper()
    needs_rebuild = any(
        [
            not _has_fk(cursor, "faturas_cartao", "cartao_id", "cartoes", on_delete="CASCADE"),
            not _has_fk(cursor, "faturas_cartao", "usuario_id", "usuarios", on_delete="CASCADE"),
            "CHECK (MES BETWEEN 1 AND 12)" not in sql and "CHECK(MES BETWEEN 1 AND 12)" not in sql,
            "STATUS IN ('ABERTA', 'FECHADA', 'PAGA', 'VENCIDA')" not in sql,
        ]
    )
    if not needs_rebuild:
        return False

    expected_count = _prepare_rebuild(cursor, "faturas_cartao")
    _validate_faturas_for_rebuild(cursor)
    cursor.execute("DROP TABLE faturas_cartao")
    cursor.execute(
        """
        CREATE TABLE faturas_cartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cartao_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
            ano INTEGER NOT NULL,
            valor_total REAL DEFAULT 0,
            status TEXT DEFAULT 'aberta' CHECK (status IN ('aberta', 'fechada', 'paga', 'vencida')),
            vencimento DATE,
            fechamento DATE,
            criado_em DATETIME,
            atualizado_em DATETIME,
            FOREIGN KEY(cartao_id) REFERENCES cartoes(id) ON DELETE CASCADE,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO faturas_cartao (
            id, cartao_id, usuario_id, mes, ano, valor_total, status, vencimento,
            fechamento, criado_em, atualizado_em
        )
        SELECT
            id, cartao_id, usuario_id, mes, ano, COALESCE(valor_total, 0),
            COALESCE(status, 'aberta'), vencimento, fechamento,
            COALESCE(criado_em, CURRENT_TIMESTAMP), COALESCE(atualizado_em, CURRENT_TIMESTAMP)
        FROM temp.__backup_faturas_cartao
        """
    )
    _validate_copy_count(cursor, "faturas_cartao", expected_count)
    return True


def _validate_limites_for_rebuild(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM temp.__backup_limites_mensais l
        WHERE usuario_id IS NULL
           OR valor_limite IS NULL
           OR NOT EXISTS (SELECT 1 FROM usuarios u WHERE u.id = l.usuario_id)
        """
    )
    invalid_count = cursor.fetchone()[0]
    if invalid_count:
        raise RuntimeError(
            f"Migracao de limites_mensais interrompida: {invalid_count} registro(s) violam as novas constraints."
        )


def _rebuild_limites_if_needed(cursor):
    if not _table_exists(cursor, "limites_mensais"):
        return False

    needs_rebuild = any(
        [
            not _has_fk(cursor, "limites_mensais", "usuario_id", "usuarios", on_delete="CASCADE"),
            not _has_not_null(cursor, "limites_mensais", "usuario_id"),
            not _has_not_null(cursor, "limites_mensais", "valor_limite"),
        ]
    )
    if not needs_rebuild:
        return False

    expected_count = _prepare_rebuild(cursor, "limites_mensais")
    _validate_limites_for_rebuild(cursor)
    cursor.execute("DROP TABLE limites_mensais")
    cursor.execute(
        """
        CREATE TABLE limites_mensais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            valor_limite REAL NOT NULL,
            criado_em DATETIME,
            atualizado_em DATETIME,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO limites_mensais (id, usuario_id, valor_limite, criado_em, atualizado_em)
        SELECT
            id, usuario_id, valor_limite,
            COALESCE(criado_em, CURRENT_TIMESTAMP),
            COALESCE(atualizado_em, CURRENT_TIMESTAMP)
        FROM temp.__backup_limites_mensais
        """
    )
    _validate_copy_count(cursor, "limites_mensais", expected_count)
    return True


def _validate_conquistas_for_rebuild(cursor):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM temp.__backup_conquistas c
        WHERE usuario_id IS NULL
           OR nome IS NULL
           OR trim(nome) = ''
           OR valor_total IS NULL
           OR NOT EXISTS (SELECT 1 FROM usuarios u WHERE u.id = c.usuario_id)
        """
    )
    invalid_count = cursor.fetchone()[0]
    if invalid_count:
        raise RuntimeError(
            f"Migracao de conquistas interrompida: {invalid_count} registro(s) violam as novas constraints."
        )


def _rebuild_conquistas_if_needed(cursor):
    if not _table_exists(cursor, "conquistas"):
        return False

    needs_rebuild = any(
        [
            not _has_fk(cursor, "conquistas", "usuario_id", "usuarios", on_delete="CASCADE"),
            not _has_not_null(cursor, "conquistas", "usuario_id"),
            not _has_not_null(cursor, "conquistas", "nome"),
            not _has_not_null(cursor, "conquistas", "valor_total"),
        ]
    )
    if not needs_rebuild:
        return False

    expected_count = _prepare_rebuild(cursor, "conquistas")
    _validate_conquistas_for_rebuild(cursor)
    cursor.execute("DROP TABLE conquistas")
    cursor.execute(
        """
        CREATE TABLE conquistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            valor_total REAL NOT NULL,
            valor_guardado REAL DEFAULT 0,
            prazo_meses INTEGER,
            criado_em DATETIME,
            atualizado_em DATETIME,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO conquistas (
            id, usuario_id, nome, valor_total, valor_guardado, prazo_meses, criado_em, atualizado_em
        )
        SELECT
            id, usuario_id, nome, valor_total, COALESCE(valor_guardado, 0),
            prazo_meses, COALESCE(criado_em, CURRENT_TIMESTAMP), COALESCE(atualizado_em, CURRENT_TIMESTAMP)
        FROM temp.__backup_conquistas
        """
    )
    _validate_copy_count(cursor, "conquistas", expected_count)
    return True


def _normalize_data(cursor):
    statements = [
        ("UPDATE usuarios SET meta_mensal=0 WHERE meta_mensal IS NULL", ()),
        ("UPDATE usuarios SET tentativas_falhas=0 WHERE tentativas_falhas IS NULL", ()),
        ("UPDATE tokens_recuperacao SET usado=0 WHERE usado IS NULL", ()),
        ("UPDATE contas SET saldo_inicial=0 WHERE saldo_inicial IS NULL", ()),
        ("UPDATE contas SET tipo='corrente' WHERE tipo IS NULL OR trim(tipo)=''", ()),
        ("UPDATE contas SET cor=? WHERE cor IS NULL OR trim(cor)=''", (ACCOUNT_COLOR_DEFAULT,)),
        ("UPDATE contas SET ativo=1 WHERE ativo IS NULL", ()),
        ("UPDATE contas SET criado_em=CURRENT_TIMESTAMP WHERE criado_em IS NULL", ()),
        ("UPDATE contas SET atualizado_em=CURRENT_TIMESTAMP WHERE atualizado_em IS NULL", ()),
        ("UPDATE cartoes SET limite=0 WHERE limite IS NULL", ()),
        ("UPDATE cartoes SET tipo_cartao='credito' WHERE tipo_cartao IS NULL OR trim(tipo_cartao)=''", ()),
        ("UPDATE cartoes SET cor=? WHERE cor IS NULL OR trim(cor)=''", (CARD_COLOR_DEFAULT,)),
        ("UPDATE cartoes SET ativo=1 WHERE ativo IS NULL", ()),
        ("UPDATE cartoes SET criado_em=CURRENT_TIMESTAMP WHERE criado_em IS NULL", ()),
        ("UPDATE cartoes SET atualizado_em=CURRENT_TIMESTAMP WHERE atualizado_em IS NULL", ()),
        ("UPDATE lancamentos SET criado_em=CURRENT_TIMESTAMP WHERE criado_em IS NULL", ()),
        ("UPDATE lancamentos SET atualizado_em=CURRENT_TIMESTAMP WHERE atualizado_em IS NULL", ()),
        ("UPDATE limites_mensais SET criado_em=CURRENT_TIMESTAMP WHERE criado_em IS NULL", ()),
        ("UPDATE limites_mensais SET atualizado_em=CURRENT_TIMESTAMP WHERE atualizado_em IS NULL", ()),
        ("UPDATE conquistas SET valor_guardado=0 WHERE valor_guardado IS NULL", ()),
        ("UPDATE conquistas SET criado_em=CURRENT_TIMESTAMP WHERE criado_em IS NULL", ()),
        ("UPDATE conquistas SET atualizado_em=CURRENT_TIMESTAMP WHERE atualizado_em IS NULL", ()),
        ("UPDATE faturas_cartao SET valor_total=0 WHERE valor_total IS NULL", ()),
        (
            "UPDATE faturas_cartao SET status='aberta' WHERE status IS NULL OR status NOT IN ('aberta', 'fechada', 'paga', 'vencida')",
            (),
        ),
        ("UPDATE faturas_cartao SET criado_em=CURRENT_TIMESTAMP WHERE criado_em IS NULL", ()),
        ("UPDATE faturas_cartao SET atualizado_em=CURRENT_TIMESTAMP WHERE atualizado_em IS NULL", ()),
        ("UPDATE transferencias SET criado_em=CURRENT_TIMESTAMP WHERE criado_em IS NULL", ()),
        ("UPDATE transferencias SET atualizado_em=CURRENT_TIMESTAMP WHERE atualizado_em IS NULL", ()),
    ]
    for sql, params in statements:
        cursor.execute(sql, params)


def _create_indexes(cursor):
    cursor.executescript(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_google_id
        ON usuarios(google_id)
        WHERE google_id IS NOT NULL;

        CREATE INDEX IF NOT EXISTS idx_lancamentos_usuario_data
        ON lancamentos(usuario_id, data);

        CREATE INDEX IF NOT EXISTS idx_lancamentos_conta
        ON lancamentos(conta_id);

        CREATE INDEX IF NOT EXISTS idx_lancamentos_cartao
        ON lancamentos(cartao_id);

        CREATE INDEX IF NOT EXISTS idx_lancamentos_categoria
        ON lancamentos(categoria_id);

        CREATE INDEX IF NOT EXISTS idx_contas_usuario
        ON contas(usuario_id);

        CREATE INDEX IF NOT EXISTS idx_cartoes_usuario
        ON cartoes(usuario_id);

        CREATE INDEX IF NOT EXISTS idx_faturas_cartao_usuario
        ON faturas_cartao(usuario_id, cartao_id, ano, mes);

        CREATE INDEX IF NOT EXISTS idx_transferencias_usuario_data
        ON transferencias(usuario_id, data);

        CREATE INDEX IF NOT EXISTS idx_transferencias_origem
        ON transferencias(conta_origem_id);

        CREATE INDEX IF NOT EXISTS idx_transferencias_destino
        ON transferencias(conta_destino_id);

        CREATE INDEX IF NOT EXISTS idx_limites_mensais_usuario
        ON limites_mensais(usuario_id);

        CREATE INDEX IF NOT EXISTS idx_conquistas_usuario
        ON conquistas(usuario_id);

        CREATE INDEX IF NOT EXISTS idx_categorias_parent
        ON categorias(parent_id);
        """
    )


def _ensure_audit_triggers(cursor, table_name):
    cursor.executescript(
        f"""
        DROP TRIGGER IF EXISTS trg_{table_name}_criado_em;
        DROP TRIGGER IF EXISTS trg_{table_name}_atualizado_em;

        CREATE TRIGGER trg_{table_name}_criado_em
        AFTER INSERT ON {table_name}
        FOR EACH ROW
        WHEN NEW.criado_em IS NULL OR NEW.atualizado_em IS NULL
        BEGIN
            UPDATE {table_name}
            SET
                criado_em = COALESCE(NEW.criado_em, CURRENT_TIMESTAMP),
                atualizado_em = COALESCE(NEW.atualizado_em, CURRENT_TIMESTAMP)
            WHERE id = NEW.id;
        END;

        CREATE TRIGGER trg_{table_name}_atualizado_em
        AFTER UPDATE ON {table_name}
        FOR EACH ROW
        WHEN NEW.atualizado_em IS OLD.atualizado_em
        BEGIN
            UPDATE {table_name}
            SET atualizado_em = CURRENT_TIMESTAMP
            WHERE id = OLD.id;
        END;
        """
    )


def _insert_default_categories(cursor):
    cursor.execute("SELECT lower(trim(nome)) FROM categorias")
    existing_categories = {row[0] for row in cursor.fetchall() if row[0]}
    for category_name in DEFAULT_CATEGORIES:
        normalized = category_name.strip().lower()
        if normalized not in existing_categories:
            cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (category_name,))
            existing_categories.add(normalized)


def _validate_foreign_keys(cursor):
    cursor.execute("PRAGMA foreign_key_check")
    problems = cursor.fetchall()
    if problems:
        raise RuntimeError(f"Schema migrado com inconsistencias de foreign key: {problems}")


def criar_banco():
    with conectar() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN")
            cursor.executescript(BASE_SCHEMA)

            for table_name, column_name, definition in SCHEMA_UPGRADES:
                _ensure_column(cursor, table_name, column_name, definition)

            _normalize_data(cursor)

            _rebuild_categorias_if_needed(cursor)
            _rebuild_lancamentos_if_needed(cursor)
            _rebuild_transferencias_if_needed(cursor)
            _rebuild_faturas_if_needed(cursor)
            _rebuild_limites_if_needed(cursor)
            _rebuild_conquistas_if_needed(cursor)

            _normalize_data(cursor)
            _create_indexes(cursor)

            for table_name in AUDITED_TABLES:
                _ensure_audit_triggers(cursor, table_name)

            _insert_default_categories(cursor)
            _validate_foreign_keys(cursor)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
