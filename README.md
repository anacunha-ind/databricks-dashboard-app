# Dashboard de Métricas - Databricks App

Projeto prático do plano de estudos de Databricks Apps & Software Engineering.

## 📋 Sobre o Projeto

Dashboard de métricas desenvolvido com Databricks Apps, utilizando Streamlit para visualização de dados provenientes do Delta Lake.

**Padrões seguidos**:

- Google Python Style Guide (docstrings)
- Ruff linting (line-length: 120)
- Python 3.12
- Estrutura inspirada em `indimesh_dbk_features_reference`

## 🚀 Stack Tecnológica

- **Frontend**: Streamlit 1.50+
- **Backend**: Delta Lake + Databricks SQL
- **Deploy**: DAB (Data Asset Bundles)
- **Ambientes**: dev + prod
- **Package Manager**: uv (opcional) ou pip

## 🎯 Features

- [ ] Visualização de métricas básicas (contagem de registros, status de pipelines)
- [ ] Conexão com tabela Delta Lake
- [ ] Deploy automatizado com DAB
- [ ] Documentação completa
- [x] Estrutura do projeto com padrões Indicium

## 📁 Estrutura do Projeto

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
│   └── ARCHITECTURE.md         # Documentação arquitetural
├── pyproject.toml              # Configuração do projeto (Ruff, pytest)
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .env.example                # Exemplo de variáveis de ambiente
└── README.md                   # Este arquivo
```

## 🛠️ Setup Local

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

## 🧪 Desenvolvimento Local

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

## 🚢 Deploy

### Validar antes do deploy

```bash
cd bundles/dashboard-metrics
databricks bundle validate --target dev
```

### Ambiente de Desenvolvimento

```bash
cd bundles/dashboard-metrics
databricks bundle deploy --target dev
databricks bundle run dashboard_metrics_app
```

### Ambiente de Produção

```bash
cd bundles/dashboard-metrics
databricks bundle deploy --target prod
databricks bundle run dashboard_metrics_app
```

## 📖 Documentação

- [Arquitetura do Projeto](docs/ARCHITECTURE.md)
- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [DAB Documentation](https://docs.databricks.com/en/dev-tools/bundles/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 📝 Status do Projeto

### Semana 1

- [x] **Dia 1**: Setup inicial e estrutura do projeto ✅
  - [x] Databricks CLI instalado e configurado
  - [x] Estrutura de diretórios criada
  - [x] Padrões de código pesquisados e aplicados
  - [x] Configuração de linting e pre-commit
- [ ] **Dias 2-3**: Conexão com Delta Lake + primeiro protótipo
- [ ] **Dias 4-5**: Empacotamento com DAB + deploy automatizado

### Semana 2

- [ ] **Dias 1-2**: Aplicar Well-Architected Framework
- [ ] **Dias 3-4**: Testes e refactoring
- [ ] **Dia 5**: Documentação final e apresentação

---

**Criado em**: 2026-05-18  
**Autor**: Ana Cunha  
**Projeto**: Plano de Estudos Databricks Apps & Software Engineering
