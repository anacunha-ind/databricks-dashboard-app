# Arquitetura do Dashboard de Métricas

## Visão Geral

Dashboard de métricas de varejo desenvolvido como Databricks App utilizando Streamlit para visualização de dados do catálogo `samples.tpch` via Databricks Lakebase. Autenticação via M2M OAuth com Service Principal, queries via psycopg2 (protocolo PostgreSQL-compatível do Lakebase), e deploy automatizado com DAB + Bitbucket Pipelines.

## Stack Tecnológica

### Frontend

- **Streamlit 1.50+**: Framework Python para dashboards interativos com navegação por abas (`st.tabs`)
- **Altair**: Visualizações declarativas com formatação de eixos e tooltips

### Backend

- **Databricks Lakebase**: Banco PostgreSQL-compatível dentro do Unity Catalog; acesso via psycopg2
- **`samples.tpch`**: Dataset de varejo sintético (scale factor 10) em Unity Catalog
- **Databricks SDK (`WorkspaceClient`)**: Obtém token M2M OAuth para autenticar no Lakebase

### CI/CD

- **Bitbucket Pipelines**: Lint + testes unitários no PR; `databricks bundle deploy` no merge para `main`
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
│               ├── app.py          # Entrypoint + tabs Streamlit
│               ├── queries.py      # Data access layer (psycopg2 → Lakebase)
│               ├── charts.py       # Componentes Altair reutilizáveis
│               ├── app.yaml        # Configuração de runtime
│               └── requirements.txt
├── tests/
│   ├── conftest.py                 # Mocks de streamlit, psycopg2, databricks-sdk
│   ├── test_queries.py             # Testes de cláusulas SQL e _run_query
│   └── test_charts.py              # Smoke tests das funções de chart
├── bitbucket-pipelines.yml         # CI/CD pipeline
├── docs/
│   ├── ARCHITECTURE.md
│   └── images/
├── pyproject.toml                  # Ruff + pytest config
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

### Queries: Lakebase via psycopg2 (migrado da Statement Execution API)

**Decisão**: `psycopg2.connect()` apontando para o endpoint PostgreSQL do Lakebase

**Justificativa**: O Lakebase expõe um endpoint PostgreSQL-compatível nativo do Unity Catalog. Psycopg2 elimina a camada HTTP/REST da Statement Execution API, simplifica o parsing de resultados (cursor nativo em vez de JSON paginado) e padroniza o acesso com ferramentas PostgreSQL convencionais. O password da conexão é o token OAuth M2M obtido pelo SDK.

**Dual-path de autenticação**: `_get_token()` prefere `DATABRICKS_TOKEN` (PAT para dev local) e faz fallback para `WorkspaceClient().config.authenticate()` (M2M OAuth no runtime de Apps).

### Separação de Módulos

**Decisão**: `app.py` (entrypoint + tabs) | `queries.py` (data access layer) | `charts.py` (componentes Altair)

**Justificativa**: Um arquivo único de 400+ linhas mistura IO, lógica de apresentação e componentes visuais. A separação permite testar `queries.py` e `charts.py` de forma isolada (sem Streamlit ou Databricks) e facilita reuso de charts em outros dashboards.

### Cache de Conexão e Dados

**Decisão**: `@st.cache_resource` para o `WorkspaceClient`, `@st.cache_data(ttl=300)` para resultados de queries

**Justificativa**: Streamlit re-executa todo o script a cada interação. Sem cache, cada re-run cria nova conexão OAuth + TCP. TTL de 5 minutos equilibra frescor dos dados e custo de compute do Lakebase.

### Nomes Totalmente Qualificados (Unity Catalog)

**Decisão**: Todas as queries usam 3-part naming: `samples.tpch.orders`

**Justificativa**: psycopg2 não suporta `SET CATALOG` ou `USE` da mesma forma que a Statement Execution API. Nomes totalmente qualificados garantem que as queries funcionem independentemente do `search_path` da sessão PostgreSQL.

### Filtros: Segmento de Mercado + Período

**Decisão**: Filtros via sidebar do Streamlit, passados como parâmetros tipados (`date`, `tuple[str, ...]`) para as funções cacheadas

**Justificativa**: `@st.cache_data` usa os parâmetros como cache key — passar filtros como argumentos garante que cada combinação seja cacheada independentemente. `tuple` em vez de `list` pois listas não são hashable.

### Visualizações: Altair em vez de `st.bar_chart`

**Decisão**: `alt.Chart` para todos os gráficos, isolados em `charts.py`

**Justificativa**: `st.bar_chart` não suporta formatação de eixos, tooltips customizados ou stacked bars com labels. Altair é bundled com Streamlit e resolve todos esses casos sem dependência adicional.

### CI/CD: Bitbucket Pipelines

**Decisão**: PR executa lint (`ruff check`) + testes (`pytest`); merge para `main` executa `databricks bundle deploy --target dev`

**Justificativa**: Validação de qualidade de código antes do merge evita que falhas de lint ou testes cheguem ao ambiente de dev. O passo de deploy no merge garante que `dev` reflita sempre o estado de `main`. Padrão inspirado no `indicium-solution-nexus`.

## Limitações do Sandbox

| Limitação | Impacto | Contorno |
| --------- | ------- | -------- |
| Sem permissão de admin para criar SP | CI/CD inicialmente sem credenciais de SP próprio | PAT temporário como `DATABRICKS_TOKEN` até admin criar SP dedicado |
| `mode: development` incompatível com `permissions:` | Bloco `permissions:` removido dos targets dev/ci | Permissões gerenciadas manualmente |
| `app.yaml` sem parametrização | Valores hardcoded | Aguardando [issue #3679](https://github.com/databricks/cli/issues/3679) |
| OBO token retorna 403 na Statement Execution API | Não é possível usar token do usuário logado | M2M OAuth via SP (resolvido com Lakebase) |
| Lakebase compute deve ser desligado quando não está em uso | Custo de CU mesmo sem queries | Desligar manualmente via UI quando não houver uso |

## Sequência de Deploy

```bash
cd bundles/dashboard-metrics

# Deploy dos recursos DAB e código da app
databricks bundle deploy --target dev
```

## Status

### Semana 1

- [x] Dia 1: Setup inicial, estrutura do projeto e primeiro deploy
- [x] Dia 2: Conexão com Delta Lake + dashboard funcional (M2M OAuth, queries reais)
- [x] Dia 3: UX refinements — filtros, novas queries, charts Altair, documentação
- [x] Dias 4-5: Refactoring e documentação

### Semana 2

- [x] Dias 1-2: Migração para Lakebase via psycopg2; separação em módulos (`queries.py`, `charts.py`); navegação por abas
- [x] Dias 3-4: Testes unitários (pytest + mocks); CI/CD com Bitbucket Pipelines
- [ ] Dia 5: Demo para o time

## Referências

- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [Databricks Lakebase Documentation](https://docs.databricks.com/en/database-objects/lakebase.html)
- [DAB Documentation](https://docs.databricks.com/en/dev-tools/bundles/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Altair Documentation](https://altair-viz.github.io/)
