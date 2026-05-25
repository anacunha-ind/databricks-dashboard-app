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

## Preview

![Dashboard Dia 3](docs/images/dashboard_dia3.png)

## Sobre o Projeto

Dashboard de métricas desenvolvido com Databricks Apps, utilizando Streamlit para visualização de dados provenientes do Delta Lake.

**Padrões seguidos**:

- Google Python Style Guide (docstrings)
- Ruff linting (line-length: 120)
- Python 3.12
- Estrutura inspirada em `indimesh_dbk_features_reference`

## Stack Tecnológica

- **Frontend**: Streamlit 1.50+ (navegação por abas, filtros sidebar)
- **Dados (analítico)**: Delta Lake `samples.tpch` via Databricks SDK
- **Dados (app)**: Databricks Lakebase via `psycopg2` (PostgreSQL-compatível)
- **Deploy**: DAB (Data Asset Bundles)
- **Ambientes**: dev + prod
- **CI/CD**: Bitbucket Pipelines (`databricks bundle deploy` no merge)
- **Package Manager**: uv (opcional) ou pip

## Features

- [x] Visualização de métricas de varejo (KPIs, pedidos por status, top clientes, receita mensal)
- [x] Filtros interativos por segmento de mercado e período
- [x] Conexão com Delta Lake via Databricks SDK (M2M OAuth)
- [x] Deploy automatizado com DAB (targets dev/prod)
- [x] Documentação completa (arquitetura, lições aprendidas)
- [x] Estrutura do projeto com padrões Indicium
- [ ] Navegação por abas (`st.tabs`) — Visão Geral, Pedidos, Clientes, Produtos & Logística
- [ ] Conexão com Databricks Lakebase via `psycopg2`
- [ ] Separação em módulos (`queries.py`, `charts.py`)
- [ ] Testes automatizados em `tests/`
- [ ] CI/CD via Bitbucket Pipelines

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
│               ├── app.py      # Aplicação Streamlit principal
│               ├── app.yaml    # Configuração de runtime
│               └── requirements.txt  # Dependências Python
├── tests/                      # Testes automatizados (futuro)
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

# 1. Deploy dos recursos DAB
databricks bundle deploy --target dev

# 2. Deploy do código da app (usar workspace path após bundle deploy)
databricks apps deploy <app-name> \
  --source-code-path /Workspace/Users/<user>/.bundle/dashboard_metrics/dev/files/src/app
```

### Ambiente de Produção

```bash
cd bundles/dashboard-metrics
databricks bundle deploy --target prod
databricks apps deploy <app-name> \
  --source-code-path /Workspace/Users/<user>/.bundle/dashboard_metrics/prod/files/src/app
```

### Notas de Deploy

- O resource binding de SQL warehouse no DAB exige permissão `MANAGE` no warehouse. No sandbox, o `WAREHOUSE_ID` é configurado diretamente no `app.yaml`.
- O `app.yaml` ainda não suporta parametrização ([issue #3679](https://github.com/databricks/cli/issues/3679)) — valores hardcoded por enquanto.
- A autenticação usa M2M OAuth via Service Principal (`DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET` injetados automaticamente pelo Databricks Apps).

## Documentação

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

- [ ] **Dias 1-2**: Integração com Lakebase + UX por abas
  - [ ] Conexão PostgreSQL ao `sara-lakebase-dbx-app` via `psycopg2`
  - [ ] Navegação por `st.tabs()` com 4 abas
  - [ ] Separação em módulos: `queries.py`, `charts.py`, `app.py`
- [ ] **Dias 3-4**: Testes automatizados e CI/CD
  - [ ] Testes unitários em `tests/`
  - [ ] Bitbucket Pipelines com `databricks bundle deploy`
- [ ] **Dia 5**: Entrega para a liderança (demo 15 min)

---

**Criado em**: 2026-05-18  
**Última atualização**: 2026-05-25  
**Autor**: Sara (ana.cunha)  
**Projeto**: Plano de Estudos Databricks Apps & Software Engineering
