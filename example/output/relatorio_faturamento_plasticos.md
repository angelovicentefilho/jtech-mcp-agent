# Relatório de Faturamento - Plásticos (Jan-Mar)

**Data de geração:** 02/06/2025 16:04

## Introdução
Este relatório apresenta a análise de faturamento para plásticos nos meses de janeiro a março da tabela revenue_forecast.

## Metadados da Tabela
### Estrutura da Tabela `revenue_forecast`

Aqui está uma visão geral estruturada dos metadados da tabela `revenue_forecast`:

**Colunas:**

*   `id` (integer):
    *   `NOT NULL`
    *   `DEFAULT`: `nextval('revenue_forecast_id_seq'::regclass)`
    *   Descrição: `None`
*   `net_weight` (numeric):
    *   `NOT NULL`
    *   Descrição: `None`
*   `billing_value` (numeric):
    *   `NOT NULL`
    *   `DEFAULT`: `0.0000`    *   Descrição: `None`
*   `customer_id` (integer):
    *   `NOT NULL`
    *   Descrição: `None`
*   `waste_classification` (character varying(50)):
    *   `NOT NULL`
    *   Descrição: `None`
*   `month` (integer):
    *   `NOT NULL`
    *   Descrição: `None`
*   `year` (integer):
    *   `NOT NULL`    *   Descrição: `None`
*   `created_at` (timestamp without time zone):
    *   `NULLABLE`
    *   `DEFAULT`: `CURRENT_TIMESTAMP`
    *   Descrição: `None`
*   `updated_at` (timestamp without time zone):
    *   `NULLABLE`
    *   `DEFAULT`: `CURRENT_TIMESTAMP`
    *   Descrição: `None`

**Restrições:**

*   `revenue_forecast_pkey`:
    *   `PRIMARY KEY`
    *   Coluna: `id`

**Índices:**

*   `revenue_forecast_pkey`: `CREATE UNIQUE INDEX revenue_forecast_pkey ON public.revenue_forecast USING btree (id)`
*   `idx_revenue_forecast_customer`: `CREATE INDEX idx_revenue_forecast_customer ON public.revenue_forecast USING btree (customer_id)`
*   `idx_revenue_forecast_date`: `CREATE INDEX idx_revenue_forecast_date ON public.revenue_forecast USING btree (year, month)`
*   `idx_revenue_forecast_classification`: `CREATE INDEX idx_revenue_forecast_classification ON public.revenue_forecast USING btree (waste_classification)`

## Consulta SQL Gerada
```sql
Por favor, forneça os metadados da tabela. Preciso das informações sobre os nomes das tabelas, nomes das colunas e tipos de dados para gerar a consulta SQL correta.
```

## Resultados da Consulta
Por favor, forneça a consulta SQL que você gostaria que eu executasse.

## Conclusão
Relatório gerado automaticamente pelo framework de orquestração de agentes JTech MCP.
