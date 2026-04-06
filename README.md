# DW & BI — Transações de Cartão de Crédito

Projeto de Data Warehouse e Business Intelligence sobre faturas de cartão de crédito.
**Curso:** Análise e Desenvolvimento de Sistemas
**Período dos dados:** Março/2025 a Fevereiro/2026

---

## Estrutura do Repositório

```
projeto_dw/
├── faturas/                        # CSVs das faturas (não versionado)
│   ├── Fatura_2025-03-20.csv
│   ├── Fatura_2025-04-20.csv
│   │   ...
│   └── Fatura_2026-02-20.csv
├── docs/
│   ├── imagens/                    # Prints do dashboard
│   │   ├── visao_geral.png
│   │   ├── categorias_estabelecimentos.png
│   │   ├── analise_temporal.png
│   │   └── star_schema.png
│   ├── Fase1_Modelagem.md          # Modelagem do DW e dicionário de dados
│   └── Doc_dashboard.md            # Documentação do dashboard
├── sql/
│   └── consultas.sql               # Consultas SQL das perguntas de negócio
├── etl.py                          # Pipeline ETL (Extract → Transform → Load)
├── Dashboard Cartão.pbix           # Dashboard Power BI
├── requirements.txt                # Bibliotecas Python necessárias
├── .env                            # Credenciais do banco (não versionado)
├── .gitignore
└── README.md
```

---

## Pré-requisitos

- Python 3.10+
- PostgreSQL 14+
- Power BI Desktop (para visualizar o dashboard)

---

## Como Executar

### 1. Criar o banco de dados no PostgreSQL

No pgAdmin, crie um banco chamado `dw_cartao`. Ou via terminal:
```sql
CREATE DATABASE dw_cartao;
```

### 2. Instalar as dependências Python

```bash
pip install -r requirements.txt
```

### 3. Configurar as credenciais

Edite o arquivo `.env` com os dados da sua instalação do PostgreSQL:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dw_cartao
DB_USER=postgres
DB_PASSWORD=SUA_SENHA
DB_PASTA=./faturas
```

### 4. Organizar os arquivos CSV

Coloque todos os arquivos `Fatura_*.csv` dentro da pasta `faturas/`.

### 5. Rodar o ETL

```bash
python etl.py
```

O ETL irá:
1. Ler todos os arquivos CSV da pasta `faturas/`
2. Aplicar transformações (datas, valores, parcelas, categorias)
3. Criar o schema no banco (se não existir)
4. Fazer **full reload**
5. Carregar dimensões → depois a fato

> Ao rodar o ETL novamente, ele apaga e refaz o banco. Sem duplicações.

### 6. Validar e analisar os dados

Abra o arquivo `sql/consultas.sql` no pgAdmin e execute as consultas.

### 7. Abrir o dashboard

Abra o arquivo `Dashboard Cartão.pbix` no Power BI Desktop. O dashboard já está configurado para conectar no banco `dw_cartao` em `localhost`.

---

## Modelo de Dados (Star Schema)

```
        DIM_TITULAR
             |
DIM_DATA -- FATO_TRANSACAO -- DIM_CATEGORIA
                  |
         DIM_ESTABELECIMENTO
```

| Tabela | Descrição |
|--------|-----------|
| `fato_transacao` | Uma linha por evento de transação do CSV |
| `dim_data` | Calendário com atributos temporais |
| `dim_titular` | Titulares e seus cartões |
| `dim_categoria` | Categorias MCC |
| `dim_estabelecimento` | Estabelecimentos comerciais |

---

## Perguntas de Negócio Respondidas

1. Gasto total por titular no período e por mês
2. Top 10 categorias por valor
3. Evolução mensal do total gasto (série temporal)
4. Comparativo entre titulares (ticket médio, máximo, mínimo)
5. Principais estabelecimentos (Top 15)
6. Comportamento de parcelamento: à vista vs parcelado
7. Transações por dia da semana
8. Estornos e créditos por titular e categoria
9. Transações em moeda estrangeira (USD)

---

## Dashboard

O dashboard foi desenvolvido no Power BI Desktop e está organizado em 3 páginas:

- **Visão Geral** — KPIs principais e evolução mensal dos gastos
- **Categorias e Estabelecimentos** — top 10 categorias, top 10 estabelecimentos e distribuição à vista vs parcelado
- **Análise Temporal** — transações por dia da semana, evolução por titular e tabela de compras em USD

Veja a documentação completa em [docs/Doc_dashboard.md](docs/Doc_dashboard.md).