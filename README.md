# Dashboard de Métricas - Databricks App

Projeto prático do plano de estudos de Databricks Apps & Software Engineering.

## Índice

- [Preview](#preview)
- [Sobre o Projeto](#sobre-o-projeto)
- [Stack Tecnológica](#stack-tecnológica)
- [Features](#features)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Setup Local](#setup-local)
- [Desenvolvimento Local](#desenvolvimento-local)
- [Deploy](#deploy)
- [Documentação](#documentação)
  - [Arquitetura do Projeto](docs/ARCHITECTURE.md)
  - [Lições Aprendidas](docs/LESSONS_LEARNED.md)
  - [Plano de Estudos](docs/STUDY_PLAN.md)
- [Status do Projeto](#status-do-projeto)

---

## Changelog das versões

Histórico completo de versões com capturas de tela: [docs/CHANGELOG.md](docs/CHANGELOG.md)

## Sobre o Projeto

Dashboard de métricas de varejo desenvolvido com Databricks Apps, utilizando Streamlit para visualização de dados do catálogo `samples.tpch` via Databricks Lakebase (PostgreSQL).

**Padrões seguidos**:

- Google Python Style Guide (docstrings)
- Ruff linting (line-length: 120)
- Python 3.12
- Estrutura inspirada em `indimesh_dbk_features_reference`

## Stack Tecnológica

- **Frontend**: Streamlit 1.50+ (navegação por abas, filtros sidebar)
- **Dados**: `samples.tpch` (TPC-H scale factor 10) sincronizado para Databricks Lakebase via `create-synced-table`
- **Backend**: Databricks Lakebase via `psycopg2` (PostgreSQL-compatível); auth OAuth via `generate_database_credential`
- **Deploy**: DAB (Data Asset Bundles) — targets dev / preview / prod
- **CI/CD**: Bitbucket Pipelines (lint + testes no PR, `bundle deploy` no merge para main)
- **Package Manager**: uv (opcional) ou pip

## Features

- [x] Visualização de métricas de varejo (KPIs, pedidos por status, top clientes, receita mensal)
- [x] Filtros interativos por segmento de mercado e período
- [x] Conexão com Databricks Lakebase via `psycopg2` (M2M OAuth)
- [x] Deploy automatizado com DAB (targets dev/prod)
- [x] Documentação completa (arquitetura, lições aprendidas)
- [x] Estrutura do projeto com padrões Indicium
- [x] Navegação por abas (`st.tabs`) — Visão Geral, Pedidos, Clientes, Produtos & Logística
- [x] Conexão com Databricks Lakebase via `psycopg2`
- [x] Separação em módulos (`queries.py`, `charts.py`)
- [x] Testes automatizados em `tests/` (24 testes unitários)
- [x] CI/CD via Bitbucket Pipelines (lint + testes + bundle validate/deploy)

## Estrutura do Projeto

```text
databricks-dashboard-app/
├── bundles/
│   └── dashboard-metrics/      # Bundle DAB (padrão indimesh)
│       ├── databricks.yml      # Configuração principal do bundle
│       ├── targets.yml         # Targets (dev/ci/qa/prod)
│       ├── variables.yml       # Variáveis do bundle
│       ├── resources/
│       │   └── dashboard_app.yml  # Definição da app e recursos
│       └── src/
│           └── app/
│               ├── app.py      # Aplicação Streamlit (tabs + sidebar)
│               ├── queries.py  # Data access layer (Lakebase via psycopg2)
│               ├── charts.py   # Funções de visualização Altair
│               ├── app.yaml    # Configuração de runtime
│               └── requirements.txt  # Dependências Python
├── tests/
│   ├── conftest.py             # Mocks e fixtures compartilhadas
│   ├── test_queries.py         # Testes unitários do data access layer
│   └── test_charts.py          # Smoke tests das funções de chart
├── bitbucket-pipelines.yml     # CI/CD: lint + testes + bundle deploy
├── docs/
│   ├── ARCHITECTURE.md         # Documentação arquitetural e decisões de design
│   └── LESSONS_LEARNED.md      # Lições aprendidas (conexão, configuração, deploy)
├── pyproject.toml              # Configuração do projeto (Ruff, pytest)
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .env.example                # Exemplo de variáveis de ambiente
└── README.md                   # Este arquivo
```

## Setup Local

### Pré-requisitos

- Python 3.12
- Databricks CLI instalado (v0.299+)
- Acesso a workspace Databricks
- uv (recomendado) ou pip

### Instalação com uv (recomendado)

```bash
# Clone o repositório
git clone <repo-url>
cd databricks-dashboard-app

# Criar ambiente virtual e instalar dependências
uv sync --dev

# Instalar pre-commit hooks
uv run pre-commit install
```

### Instalação com pip

```bash
# Clone o repositório
git clone <repo-url>
cd databricks-dashboard-app

# Criar ambiente virtual
python3.12 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
pip install pytest ruff pre-commit  # dev dependencies

# Instalar pre-commit hooks
pre-commit install
```

### Configuração

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
# DATABRICKS_HOST=https://your-workspace.cloud.databricks.com/
# DATABRICKS_WAREHOUSE_ID=your-warehouse-id

# Carregar variáveis de ambiente
source .env

# Configurar autenticação Databricks CLI
databricks auth login --host $DATABRICKS_HOST
```

## Desenvolvimento Local

```bash
# Rodar aplicação localmente (após configurar .env)
cd bundles/dashboard-metrics/src/app
streamlit run app.py --server.port 8000 --server.address 0.0.0.0

# Linting e formatação
uv run ruff check .
uv run ruff format .

# Rodar pre-commit checks
uv run pre-commit run --all-files
```

## Deploy

### Validar antes do deploy

```bash
cd bundles/dashboard-metrics
databricks bundle validate --target dev
```

### Ambiente de Desenvolvimento

```bash
cd bundles/dashboard-metrics

# Deploy dos recursos e código da app
databricks bundle deploy --target dev
databricks bundle run dashboard_metrics_app --target dev
```

### Preview por PR (automatizado via Bitbucket Pipelines)

O script `scripts/deploy_preview.sh` cria um ambiente isolado por PR:

1. Branch Lakebase copy-on-write a partir de production
2. Deploy do bundle no target `preview`
3. Criação de role Lakebase para o SP auto-gerado pelo app

### Ambiente de Produção

```bash
cd bundles/dashboard-metrics
databricks bundle deploy --target prod
databricks bundle run dashboard_metrics_app --target prod
```

### Notas de Deploy

- O `app.yaml` ainda não suporta parametrização ([issue #3679](https://github.com/databricks/cli/issues/3679)) — `LAKEBASE_HOST` e `LAKEBASE_ENDPOINT` são hardcoded por ambiente.
- A autenticação usa M2M OAuth via Service Principal (`DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET` injetados automaticamente pelo Databricks Apps runtime).
- O SP auto-gerado por cada Databricks App precisa de uma role Lakebase com `LAKEBASE_OAUTH_V1` e `DATABRICKS_SUPERUSER`. O `deploy_preview.sh` cria essa role automaticamente.

## Documentação

- [Changelog de Versões](docs/CHANGELOG.md)
- [Arquitetura do Projeto](docs/ARCHITECTURE.md)
- [Lições Aprendidas](docs/LESSONS_LEARNED.md)
- [Plano de Estudos](docs/STUDY_PLAN.md)
- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [DAB Documentation](https://docs.databricks.com/en/dev-tools/bundles/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## Status do Projeto

### Semana 1

- [x] **Dia 1**: Setup inicial, estrutura do projeto e primeiro deploy
  - [x] Databricks CLI instalado e configurado
  - [x] Estrutura de diretórios criada
  - [x] Padrões de código pesquisados e aplicados
  - [x] Configuração de linting e pre-commit
- [x] **Dia 2**: Conexão com Delta Lake + dashboard funcional
  - [x] Autenticação M2M OAuth via Service Principal (WorkspaceClient)
  - [x] Queries ao catálogo `samples.tpch` via Statement Execution API
  - [x] Dashboard com KPIs, gráficos de barras e linha no Streamlit
  - [x] Deploy completo via DAB (`bundle deploy` + `apps deploy`)
- [x] **Dia 3**: UX refinements
  - [x] Filtros por segmento de mercado e período (sidebar)
  - [x] Visualizações Altair (stacked bars, line chart) com tooltips customizados
  - [x] Novas queries: faturamento por status, pedidos por mês
  - [x] Documentação arquitetural (`ARCHITECTURE.md`, `LESSONS_LEARNED.md`)

### Semana 2

- [x] **Dias 1-2**: Integração com Lakebase + UX por abas
  - [x] Conexão PostgreSQL ao `sara-lakebase-dbx-app` via `psycopg2`
  - [x] Navegação por `st.tabs()` com 4 abas (Visão Geral, Pedidos, Clientes, Produtos & Logística)
  - [x] Separação em módulos: `queries.py`, `charts.py`, `app.py`
- [x] **Dias 3-4**: Testes + CI/CD + Lakebase integração completa
  - [x] 24 testes unitários em `tests/` (`test_queries.py`, `test_charts.py`)
  - [x] Bitbucket Pipelines: lint + testes no PR, `bundle deploy` no merge
  - [x] 4 tabelas TPC-H sincronizadas via `create-synced-table` para Lakebase production
  - [x] Fix 3-part naming → nomes não qualificados + `search_path=tpch`
  - [x] Auth migrada para `generate_database_credential` (token OAuth ~60 min)
  - [x] `deploy_preview.sh`: preview por PR com branch CoW, role Lakebase automática, schema único por PR
- [ ] **Dia 5**: Entrega para a liderança (demo 15 min)

---

**Criado em**: 2026-05-18  
**Última atualização**: 2026-05-27  
**Autor**: Sara (ana.cunha)  
**Projeto**: Plano de Estudos Databricks Apps & Software Engineering
