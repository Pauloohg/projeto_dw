import os
import re
import glob
import argparse
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DDL = """
CREATE TABLE IF NOT EXISTS dim_data (
    id_data INTEGER PRIMARY KEY,
    data DATE NOT NULL,
    dia SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    nome_mes VARCHAR(15) NOT NULL,
    trimestre SMALLINT NOT NULL,
    ano SMALLINT NOT NULL,
    dia_semana_num SMALLINT NOT NULL,
    dia_semana_nome VARCHAR(15) NOT NULL,
    fim_de_semana BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_titular (
    id_titular SERIAL PRIMARY KEY,
    nome_titular VARCHAR(100) NOT NULL,
    final_cartao CHAR(4) NOT NULL,
    UNIQUE (nome_titular, final_cartao)
);

CREATE TABLE IF NOT EXISTS dim_categoria (
    id_categoria SERIAL PRIMARY KEY,
    nome_categoria VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_estabelecimento (
    id_estabelecimento SERIAL PRIMARY KEY,
    nome_estabelecimento VARCHAR(200) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fato_transacao (
    id_transacao SERIAL PRIMARY KEY,
    id_data INTEGER NOT NULL REFERENCES dim_data(id_data),
    id_titular INTEGER NOT NULL REFERENCES dim_titular(id_titular),
    id_categoria INTEGER NOT NULL REFERENCES dim_categoria(id_categoria),
    id_estabelecimento INTEGER NOT NULL REFERENCES dim_estabelecimento(id_estabelecimento),
    valor_brl NUMERIC(12,2) NOT NULL,
    valor_usd NUMERIC(10,2),
    cotacao NUMERIC(8,4),
    parcela_texto VARCHAR(10),
    num_parcela SMALLINT,
    total_parcelas SMALLINT,
    arquivo_origem VARCHAR(60)
);
"""

NOMES_MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}
NOMES_DIAS = {
    0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
    3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo",
}


# ── EXTRACT 

def extrair_csvs(pasta):
    arquivos = sorted(glob.glob(os.path.join(pasta, "Fatura_*.csv")))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo Fatura_*.csv encontrado em: {pasta}")

    frames = []
    for arq in arquivos:
        df = pd.read_csv(arq, sep=";", encoding="utf-8", dtype=str, keep_default_na=False)
        df["arquivo_origem"] = os.path.basename(arq)
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


# ── TRANSFORM 

def _parse_decimal(valor):
    if not valor or str(valor).strip() in ("-", "", "0"):
        return None
    v = str(valor).strip()
    if "," in v:
        v = v.replace(".", "").replace(",", ".")
    try:
        result = float(v)
        return result if result != 0.0 else None
    except ValueError:
        return None


def _parse_parcela(texto):
    t = texto.strip() if texto else ""
    if t.lower() in ("única", "unica", ""):
        return ("Única", 1, 1)
    m = re.match(r"^(\d+)/(\d+)$", t)
    if m:
        return (t, int(m.group(1)), int(m.group(2)))
    return (t, None, None)


def _parse_data(texto):
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except Exception:
        return None


def transformar(df_bruto):
    df = df_bruto.copy()

    df.columns = [
        "data_compra", "nome_titular", "final_cartao",
        "categoria", "descricao", "parcela",
        "valor_usd_raw", "cotacao_raw", "valor_brl_raw",
        "arquivo_origem",
    ]

    for col in ["nome_titular", "final_cartao", "categoria", "descricao", "parcela"]:
        df[col] = df[col].str.strip()

    df["categoria"] = df["categoria"].replace({"": "Não Categorizado", "-": "Não Categorizado"})
    df["categoria"] = df["categoria"].fillna("Não Categorizado")

    df["data_compra"] = df["data_compra"].apply(_parse_data)
    df = df.dropna(subset=["data_compra"])

    df["valor_brl"] = df["valor_brl_raw"].apply(lambda v: _parse_decimal(v) or 0.0)
    df["valor_usd"] = df["valor_usd_raw"].apply(_parse_decimal)
    df["cotacao"]   = df["cotacao_raw"].apply(_parse_decimal)

    parcelas = df["parcela"].apply(_parse_parcela)
    df["parcela_texto"] = parcelas.apply(lambda x: x[0])
    df["num_parcela"] = parcelas.apply(lambda x: x[1])
    df["total_parcelas"] = parcelas.apply(lambda x: x[2])

    df["final_cartao"] = df["final_cartao"].str.zfill(4).str[:4]

    return df


# ── BUILD DIM_DATA 

def construir_dim_data(datas):
    registros = {}
    for d in datas:
        if d is None:
            continue
        id_data = int(d.strftime("%Y%m%d"))
        if id_data not in registros:
            dow = d.weekday()
            registros[id_data] = {
                "id_data": id_data,
                "data": d,
                "dia": d.day,
                "mes": d.month,
                "nome_mes": NOMES_MESES[d.month],
                "trimestre": (d.month - 1) // 3 + 1,
                "ano": d.year,
                "dia_semana_num": dow,
                "dia_semana_nome": NOMES_DIAS[dow],
                "fim_de_semana": dow >= 5,
            }
    return list(registros.values())


# ── LOAD

def conectar(host, port, db, user, password):
    conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)
    conn.autocommit = False
    return conn


def criar_schema(conn):
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()


def truncar_tabelas(conn):
    with conn.cursor() as cur:
        cur.execute(
            "TRUNCATE TABLE fato_transacao, dim_estabelecimento, "
            "dim_categoria, dim_titular, dim_data RESTART IDENTITY CASCADE;"
        )
    conn.commit()


def carregar_dim_data(conn, registros):
    sql = """
        INSERT INTO dim_data
            (id_data, data, dia, mes, nome_mes, trimestre, ano,
             dia_semana_num, dia_semana_nome, fim_de_semana)
        VALUES %s
        ON CONFLICT (id_data) DO NOTHING;
    """
    valores = [(
        r["id_data"], r["data"], r["dia"], r["mes"], r["nome_mes"],
        r["trimestre"], r["ano"], r["dia_semana_num"],
        r["dia_semana_nome"], r["fim_de_semana"]
    ) for r in registros]
    with conn.cursor() as cur:
        execute_values(cur, sql, valores)
    conn.commit()


def _carregar_lookup(conn, tabela, coluna, valores_unicos):
    sql_ins = f"INSERT INTO {tabela} ({coluna}) VALUES %s ON CONFLICT ({coluna}) DO NOTHING;"
    sql_sel = f"SELECT id_{tabela.replace('dim_', '')}, {coluna} FROM {tabela};"
    with conn.cursor() as cur:
        execute_values(cur, sql_ins, [(v,) for v in valores_unicos])
        cur.execute(sql_sel)
        mapa = {row[1]: row[0] for row in cur.fetchall()}
    conn.commit()
    return mapa


def carregar_dim_titular(conn, df):
    pares = df[["nome_titular", "final_cartao"]].drop_duplicates()
    sql_ins = """
        INSERT INTO dim_titular (nome_titular, final_cartao)
        VALUES %s ON CONFLICT (nome_titular, final_cartao) DO NOTHING;
    """
    sql_sel = "SELECT id_titular, nome_titular, final_cartao FROM dim_titular;"
    with conn.cursor() as cur:
        execute_values(cur, sql_ins, list(pares.itertuples(index=False, name=None)))
        cur.execute(sql_sel)
        mapa = {(row[1], row[2]): row[0] for row in cur.fetchall()}
    conn.commit()
    return mapa


def _none(val):
    import math
    if val is None:
        return None
    try:
        return None if math.isnan(float(val)) else val
    except (TypeError, ValueError):
        return val if val != "" else None


def carregar_fato(conn, df, map_titular, map_categoria, map_estabelecimento):
    registros = []
    for _, row in df.iterrows():
        id_data = int(row["data_compra"].strftime("%Y%m%d"))
        id_titular = map_titular.get((row["nome_titular"], row["final_cartao"]))
        id_cat = map_categoria.get(row["categoria"])
        id_est = map_estabelecimento.get(row["descricao"].strip())

        if None in (id_titular, id_cat, id_est):
            continue

        registros.append((
            id_data, id_titular, id_cat, id_est,
            _none(row["valor_brl"]), _none(row["valor_usd"]), _none(row["cotacao"]),
            _none(row["parcela_texto"]), _none(row["num_parcela"]), _none(row["total_parcelas"]),
            _none(row["arquivo_origem"]),
        ))

    sql = """
        INSERT INTO fato_transacao
            (id_data, id_titular, id_categoria, id_estabelecimento,
             valor_brl, valor_usd, cotacao,
             parcela_texto, num_parcela, total_parcelas, arquivo_origem)
        VALUES %s;
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, registros)
    conn.commit()


# ── EXECUÇÃO PRINCIPAL

def executar_etl(host, port, db, user, password, pasta):
    print("Iniciando ETL...")

    df_bruto = extrair_csvs(pasta)
    df = transformar(df_bruto)

    conn = conectar(host, port, db, user, password)
    try:
        criar_schema(conn)
        truncar_tabelas(conn)

        carregar_dim_data(conn, construir_dim_data(df["data_compra"].unique()))
        map_titular = carregar_dim_titular(conn, df)
        map_categoria = _carregar_lookup(conn, "dim_categoria", "nome_categoria", df["categoria"].unique().tolist())
        map_estabelec = _carregar_lookup(conn, "dim_estabelecimento", "nome_estabelecimento", df["descricao"].str.strip().unique().tolist())

        carregar_fato(conn, df, map_titular, map_categoria, map_estabelec)

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    print("ETL concluído com sucesso!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL - DW Cartão de Crédito")
    parser.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--port", default=int(os.getenv("DB_PORT", "5432")), type=int)
    parser.add_argument("--db",   default=os.getenv("DB_NAME", "dw_cartao"))
    parser.add_argument("--user", default=os.getenv("DB_USER", "postgres"))
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", ""))
    parser.add_argument("--pasta", default=os.getenv("DB_PASTA","./faturas"))
    args = parser.parse_args()

    executar_etl(args.host, args.port, args.db, args.user, args.password, args.pasta)