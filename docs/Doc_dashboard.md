# Dashboard — DW Transações de Cartão de Crédito

Dashboard desenvolvido no **Power BI Desktop**, conectado diretamente ao banco de dados PostgreSQL (`dw_cartao`). Os dados cobrem o período de março/2025 a fevereiro/2026, com transações de 4 titulares.

---

## Métricas disponíveis

| Métrica | O que representa |
|---|---|
| **Total Gasto** | Soma de todos os débitos do período (exclui estornos) |
| **Total Transações** | Quantidade de compras realizadas |
| **Ticket Médio** | Valor médio por compra |
| **Total Estornos** | Valor total devolvido/estornado (aparece negativo) |

---

## Filtros

Todas as páginas têm dois filtros que atualizam todos os gráficos automaticamente:

- **Filtro de data** — controle deslizante para selecionar o período
- **Filtro de titular** — seleciona um ou mais titulares do cartão

Clicar em qualquer barra ou fatia de um gráfico também filtra os demais visuais da página.

---

## Página 1 — Visão Geral

Resumo geral dos gastos com os principais indicadores e evolução ao longo do tempo.

![Visão Geral](imagens/visao_geral.png)

- Os 4 cartões no topo mostram os KPIs do período
- O gráfico de linha mostra como o gasto variou mês a mês
- O gráfico de barras compara o total gasto por cada titular

> Vin Diesel foi o titular com maior volume de gastos no período. Brian Tyler teve o menor volume.

---

## Página 2 — Categorias e Estabelecimentos

Mostra onde e em quê o dinheiro foi gasto.

![Categorias e Estabelecimentos](imagens/categorias_estabelecimentos.png)

- **Top 10 Estabelecimentos** — os lugares que mais receberam pagamentos. Mix Center liderou com folga
- **Top 10 Categorias** — os tipos de gasto mais frequentes. Associação, Automotivo e Supermercados lideram
- **Tipo de Pagamento** — 85,81% das transações foram à vista, 14,19% parceladas

---

## Página 3 — Análise Temporal

Padrões de comportamento ao longo do tempo e detalhamento das compras internacionais.

![Análise Temporal](imagens/analise_temporal.png)

- **Transações por dia da semana** — as compras se concentram nos dias úteis, com queda no fim de semana
- **Evolução mensal por titular** — mostra o gasto de cada titular mês a mês no mesmo gráfico
- **Transações em moeda estrangeira (USD)** — lista todas as compras feitas em dólar com a cotação usada na conversão

> Charlize Theron não realizou nenhuma transação em moeda estrangeira no período.