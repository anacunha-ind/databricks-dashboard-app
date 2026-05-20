# Arquitetura do Dashboard de Métricas

## Visão Geral

Dashboard de métricas de varejo desenvolvido como Databricks App utilizando Streamlit para visualização de dados do Delta Lake. Autenticação via M2M OAuth com Service Principal, queries via Statement Execution API, e deploy automatizado com DAB.

## Stack Tecnológica

### Frontend
- **Streamlit 1.50+**: Framework Python para dashboards interativos
- **Altair**: Visualizações declarativas com formatação de eixos e tooltips

### Backend

- **Delta Lake / `samples.tpch`**: Dataset de varejo sintético (scale factor 10)
- **Databricks SQL Warehouse**: Engine de processamento das queries
- **Databricks SDK (`WorkspaceClient`)**: Cliente Python para Statement Execution API

### Deploy

- **DAB (Data Asset Bundles)**: Deploy automatizado de recursos e código
- **Ambientes**: `dev` + `prod`

## Estrutura do Projeto

```
databricks-dashboard-app/
├── bundles/
│   └── dashboard-metrics/          # Bundle DAB (padrão indimesh)
│       ├── databricks.yml          # Configuração principal do bundle
│       ├── targets.yml             # Targets (dev/ci/qa/prod)
│       ├── variables.yml           # Variáveis do bundle
│       ├── resources/
│       │   └── dashboard_app.yml   # Definição da app e recursos
│       └── src/
│           └── app/
│               ├── app.py          # Aplicação Streamlit principal
│               ├── app.yaml        # Configuração de runtime
│               └── requirements.txt
├── tests/
├── docs/
│   ├── ARCHITECTURE.md
│   └── images/
├── pyproject.toml
└── README.md
```

## Padrões de Código

- **Versão**: Python 3.12
- **Style Guide**: Google Python Style Guide
- **Linter**: Ruff (line-length: 120)
- **Type Hints**: Obrigatório em funções públicas

## Decisões Arquiteturais

### Autenticação: M2M OAuth via Service Principal

**Decisão**: `WorkspaceClient()` com `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET`

**Justificativa**: O OBO token (`X-Forwarded-Access-Token`) retorna 403 no REST API do sandbox. M2M OAuth via SP é o método suportado para Databricks Apps em ambientes com restrições de permissão.

### Queries: Statement Execution API

**Decisão**: `w.statement_execution.execute_statement()` em vez de JDBC ou `databricks-sql-connector`

**Justificativa**: O SDK já gerencia autenticação M2M. Adicionar `databricks-sql-connector` seria dependência redundante para o mesmo resultado.

### Cache de Conexão e Dados

**Decisão**: `@st.cache_resource` para o `WorkspaceClient`, `@st.cache_data(ttl=300)` para resultados de queries

**Justificativa**: Streamlit re-executa todo o script a cada interação. Sem cache, cada re-run cria nova conexão OAuth + TCP, causando latência de 2-3 minutos. TTL de 5 minutos equilibra frescor dos dados e custo de compute.

### Warehouse ID Hardcoded no `app.yaml`

**Decisão**: `WAREHOUSE_ID` configurado diretamente como variável de ambiente no `app.yaml`

**Justificativa**: Resource binding de SQL warehouse no DAB exige permissão `MANAGE` no warehouse. No sandbox a usuária não tem essa permissão. Workaround via `value:` direto no `app.yaml`. A parametrização do `app.yaml` ainda não é suportada ([issue #3679](https://github.com/databricks/cli/issues/3679)).

### Filtros: Segmento de Mercado + Período

**Decisão**: Filtros via sidebar do Streamlit, passados como parâmetros tipados (`date`, `tuple[str, ...]`) para as funções cacheadas

**Justificativa**: `@st.cache_data` usa os parâmetros como cache key — passar filtros como argumentos garante que cada combinação de filtro seja cacheada independentemente. `tuple` em vez de `list` pois listas não são hashable.

### Visualizações: Altair em vez de `st.bar_chart`

**Decisão**: `alt.Chart` para todos os gráficos

**Justificativa**: `st.bar_chart` não suporta formatação de eixos, tooltips customizados ou stacked bars com labels. Altair é bundled com Streamlit e resolve todos esses casos sem dependência adicional.

## Limitações do Sandbox

| Limitação | Impacto | Contorno |
| --------- | ------- | -------- |
| Sem permissão `MANAGE` no warehouse | Não é possível fazer resource binding via DAB | `WAREHOUSE_ID` hardcoded no `app.yaml` |
| Service Principal precisa de `CAN_USE` no warehouse | Sem essa permissão o app retorna `PermissionDenied` ao executar queries | Conceder `CAN_USE` ao SP da app manualmente via UI ou CLI |
| `mode: development` incompatível com `permissions:` | Bloco `permissions:` removido dos targets dev/ci | Permissões gerenciadas manualmente |
| `app.yaml` sem parametrização | Valores hardcoded | Aguardando [issue #3679](https://github.com/databricks/cli/issues/3679) |
| OBO token retorna 403 na Statement Execution API | Não é possível usar token do usuário logado | M2M OAuth via SP |

## Sequência de Deploy

```bash
cd bundles/dashboard-metrics

# 1. Deploy dos recursos DAB
databricks bundle deploy --target dev

# 2. Deploy do código da app
databricks apps deploy <app-name> \
  --source-code-path /Workspace/Users/<user>/.bundle/dashboard_metrics/dev/files/src/app
```

## Status

### Semana 1

- [x] Dia 1: Setup inicial, estrutura do projeto e primeiro deploy
- [x] Dia 2: Conexão com Delta Lake + dashboard funcional (M2M OAuth, queries reais)
- [x] Dia 3: UX refinements — filtros, novas queries, charts Altair, documentação
- [ ] Dias 4-5: Testes e documentação final

### Semana 2
- [ ] Dias 1-2: Aplicar Well-Architected Framework
- [ ] Dias 3-4: Testes e refactoring
- [ ] Dia 5: Documentação final e apresentação

## Referências

- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [DAB Documentation](https://docs.databricks.com/en/dev-tools/bundles/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Altair Documentation](https://altair-viz.github.io/)
