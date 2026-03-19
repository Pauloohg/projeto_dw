-- Fase 3
-- 0. VALIDAÇÃO PÓS-CARGA

-- 0.1 Contagem de registros por tabela
SELECT 'dim_data' AS tabela,
    COUNT(*) AS total FROM dim_data
UNION ALL
SELECT 'dim_titular', 
    COUNT(*) FROM dim_titular
UNION ALL
SELECT 'dim_categoria', 
    COUNT(*) FROM dim_categoria
UNION ALL
SELECT 'dim_estabelecimento',
    COUNT(*) FROM dim_estabelecimento
UNION ALL
SELECT 'fato_transacao', 
    COUNT(*) FROM fato_transacao;


-- 1. GASTO TOTAL POR TITULAR NO PERÍODO
SELECT 
    t.nome_titular, 
    t.final_cartao,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl,
    SUM(CASE WHEN f.valor_brl > 0 THEN f.valor_brl ELSE 0 END) AS total_debitos,
    SUM(CASE WHEN f.valor_brl < 0 THEN f.valor_brl ELSE 0 END) AS total_estornos,
    ROUND(AVG(f.valor_brl), 2) AS ticket_medio
FROM fato_transacao f
JOIN dim_titular t ON f.id_titular = t.id_titular
GROUP BY t.nome_titular, t.final_cartao
ORDER BY total_brl DESC;


-- 2. GASTO POR TITULAR — ABERTURA MENSAL
SELECT
    d.ano,
    d.mes,
    d.nome_mes,
    t.nome_titular,
    t.final_cartao,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl
FROM fato_transacao f
JOIN dim_data    d ON f.id_data    = d.id_data
JOIN dim_titular t ON f.id_titular = t.id_titular
GROUP BY d.ano, d.mes, d.nome_mes, t.nome_titular, t.final_cartao
ORDER BY d.ano, d.mes, t.nome_titular;


-- 3. TOP 10 CATEGORIAS POR VALOR TOTAL
SELECT
    c.nome_categoria,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl,
    ROUND(100.0 * SUM(f.valor_brl) /NULLIF(SUM(SUM(f.valor_brl)) OVER (), 0),2) AS pct_total
FROM fato_transacao f
JOIN dim_categoria c ON f.id_categoria = c.id_categoria
WHERE f.valor_brl > 0
GROUP BY c.nome_categoria
ORDER BY total_brl DESC
LIMIT 10;


-- 4. EVOLUÇÃO MENSAL DO TOTAL GASTO (SÉRIE TEMPORAL)
SELECT
    d.ano,
    d.mes,
    d.nome_mes,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl,
    SUM(CASE WHEN f.valor_brl > 0 THEN f.valor_brl ELSE 0 END) AS debitos,
    SUM(CASE WHEN f.valor_brl < 0 THEN f.valor_brl ELSE 0 END) AS estornos_creditos
FROM fato_transacao f
JOIN dim_data d ON f.id_data = d.id_data
GROUP BY d.ano, d.mes, d.nome_mes
ORDER BY d.ano, d.mes;


-- 5. COMPARATIVO ENTRE TITULARES
--    Valor médio por transação, ticket máximo e mínimo
SELECT
    t.nome_titular,
    t.final_cartao,
    COUNT(*) AS qtd_transacoes,
    ROUND(AVG(f.valor_brl), 2) AS ticket_medio,
    MAX(f.valor_brl) AS maior_transacao,
    MIN(CASE WHEN f.valor_brl > 0
             THEN f.valor_brl END) AS menor_transacao_positiva,
    SUM(f.valor_brl) AS total_gasto,
    COUNT(DISTINCT d.mes || '-' || d.ano) AS meses_com_gasto
FROM fato_transacao f
JOIN dim_titular t ON f.id_titular = t.id_titular
JOIN dim_data d ON f.id_data = d.id_data
WHERE f.valor_brl > 0
GROUP BY t.nome_titular, t.final_cartao
ORDER BY total_gasto DESC;


-- 6. PRINCIPAIS ESTABELECIMENTOS (TOP 15 POR VALOR)
SELECT
    e.nome_estabelecimento,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl,
    ROUND(AVG(f.valor_brl), 2) AS ticket_medio
FROM fato_transacao f
JOIN dim_estabelecimento e ON f.id_estabelecimento = e.id_estabelecimento
WHERE f.valor_brl > 0
GROUP BY e.nome_estabelecimento
ORDER BY total_brl DESC
LIMIT 15;


-- 7. COMPORTAMENTO DE PARCELAMENTO
--    À vista vs parcelado
SELECT
    CASE
        WHEN f.total_parcelas = 1 OR f.total_parcelas IS NULL THEN 'À Vista'
        ELSE 'Parcelado'
    END AS tipo_pagamento,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl,
    ROUND(AVG(f.valor_brl), 2) AS ticket_medio
FROM fato_transacao f
WHERE f.valor_brl > 0
GROUP BY tipo_pagamento
ORDER BY total_brl DESC;

-- Distribuição por número de parcelas
SELECT
    f.total_parcelas,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl
FROM fato_transacao f
WHERE f.valor_brl > 0
  AND f.total_parcelas IS NOT NULL
GROUP BY f.total_parcelas
ORDER BY f.total_parcelas;


-- 8. TRANSAÇÕES POR DIA DA SEMANA
SELECT
    d.dia_semana_num,
    d.dia_semana_nome,
    COUNT(*) AS qtd_transacoes,
    SUM(f.valor_brl) AS total_brl,
    ROUND(AVG(f.valor_brl), 2) AS ticket_medio
FROM fato_transacao f
JOIN dim_data d ON f.id_data = d.id_data
WHERE f.valor_brl > 0
GROUP BY d.dia_semana_num, d.dia_semana_nome
ORDER BY d.dia_semana_num;


-- 9. ESTORNOS E CRÉDITOS — ANÁLISE DE IMPACTO
SELECT
    t.nome_titular,
    c.nome_categoria,
    e.nome_estabelecimento,
    d.data,
    f.valor_brl AS valor_estorno,
    f.arquivo_origem
FROM fato_transacao f
JOIN dim_data d ON f.id_data = d.id_data
JOIN dim_titular t ON f.id_titular = t.id_titular
JOIN dim_categoria c ON f.id_categoria = c.id_categoria
JOIN dim_estabelecimento e ON f.id_estabelecimento = e.id_estabelecimento
WHERE f.valor_brl < 0
ORDER BY f.valor_brl ASC;

-- Resumo de estornos por titular
SELECT
    t.nome_titular,
    COUNT(*) AS qtd_estornos,
    SUM(f.valor_brl) AS total_estornado
FROM fato_transacao f
JOIN dim_titular t ON f.id_titular = t.id_titular
WHERE f.valor_brl < 0
GROUP BY t.nome_titular
ORDER BY total_estornado ASC;


-- 10. TRANSAÇÕES EM MOEDA ESTRANGEIRA (USD)
SELECT
    d.data,
    t.nome_titular,
    e.nome_estabelecimento,
    f.valor_usd,
    f.cotacao,
    f.valor_brl,
    ROUND(f.valor_brl / NULLIF(f.valor_usd, 0), 4) AS cotacao_efetiva
FROM fato_transacao f
JOIN dim_data d ON f.id_data = d.id_data
JOIN dim_titular t ON f.id_titular = t.id_titular
JOIN dim_estabelecimento e ON f.id_estabelecimento = e.id_estabelecimento
WHERE f.valor_usd IS NOT NULL
  AND f.valor_usd > 0
ORDER BY d.data DESC;
