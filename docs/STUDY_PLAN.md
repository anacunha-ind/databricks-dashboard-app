# Plano de Estudos - Databricks Apps & Software Engineering (2 Semanas)

**Baseado em**: Orientações da liderança
**Objetivo**: Desenvolver competências em Databricks Apps, DAB, arquitetura de SaaS e uso de Claude/AI tooling para desenvolvimento  
**Duração**: 2 semanas (cronograma intensivo com projeto hands-on simultâneo)

---

## 🎯 Projeto Prático n.1: Mini SaaS App com Databricks

**Você vai construir este projeto DURANTE as 2 semanas de estudo, aplicando cada conceito conforme aprende.**

### Especificação do Projeto
**"Dashboard de Métricas com Databricks App + DAB"**

#### Stack
- **Frontend**: Streamlit ou Dash
- **Backend**: Delta Lake + Databricks SQL
- **Deploy**: DAB (Data Asset Bundles)
- **Ambientes**: dev + prod

#### Features Mínimas
1. Visualização de métricas básicas (ex: contagem de registros, status de pipelines)
2. Conectado a tabela Delta Lake
3. Deploy automatizado com DAB
4. Documentação completa

---

## 🎯 Semana 1: Setup + Fundamentos + Início do Projeto ✅ CONCLUÍDA

### Dia 1: Setup Completo ✅ (2026-05-18)

- [x] **Licença Claude**: Configurar Claude Pro/Team + plugins essenciais
- [x] **Databricks CLI**: Instalar e configurar (v0.299.2)
- [x] **Workspace**: Sandbox `dbc-6bf12fb3-babb.cloud.databricks.com`
- [x] **Projeto**: Criar repositório Git e estrutura inicial
  - [x] Estrutura de diretórios (`bundles/`, `docs/`, `tests/`)
  - [x] Configuração Streamlit + DAB
  - [x] Padrões de código (Google docstrings, Ruff, Python 3.12)
  - [x] Pre-commit hooks
  - [x] Documentação inicial (README + ARCHITECTURE)
  - [x] Git flow setup (`feature/initial-setup → dev → main`)

**Recursos**:

- [Docs Claude](https://docs.anthropic.com)
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/)

### Dias 2-3: Databricks Apps + DAB + UX ✅ (2026-05-18–20)

- [x] **Teoria**: Docs oficiais de Databricks Apps (o que são, casos de uso, diferença de Jobs/Notebooks)
- [x] **Hands-on**: Deploy real direto, sem Hello World intermediário
- [x] **PROJETO — Dia 2**: Dashboard funcional com dados reais
  - Streamlit com KPIs e tabela de top clientes
  - Delta Lake `samples.tpch` (scale factor 10, colunas com prefixo TPC-H)
  - Autenticação M2M OAuth via `WorkspaceClient()` — OBO token retorna 403 no sandbox
- [x] **PROJETO — Dia 3**: UX refinements
  - Filtros por segmento de mercado e período (sidebar)
  - Novas queries: faturamento por status, pedidos por mês
  - Visualizações Altair (stacked bars, line chart) em vez de `st.bar_chart`
  - Documentação de decisões arquiteturais em `docs/ARCHITECTURE.md`
- [x] **DAB + Deploy**: Empacotamento e deploy automatizado
  - Bundle em `bundles/dashboard-metrics/` com `databricks.yml`, `targets.yml`, `variables.yml`
  - Targets dev/prod configurados
  - App live: `https://dev-dashboard-metrics-2591888035258875.aws.databricksapps.com`

> **Limitações sandbox descobertas** (ver `docs/ARCHITECTURE.md` e memória do projeto):
>
> - Resource binding de warehouse exige `MANAGE` — contornado com `value:` hardcoded no `app.yaml`
> - `mode: development` incompatível com bloco `permissions:`
> - `app.yaml` sem parametrização ainda ([cli#3679](https://github.com/databricks/cli/issues/3679))
> - OBO token retorna 403 — usar M2M OAuth via Service Principal

**Recursos**:

- [Docs Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [Docs DAB](https://docs.databricks.com/en/dev-tools/bundles/)

---

## 🎯 Semana 2: Arquitetura + Refinamento do Projeto

### Dias 1-2: Well-Architected Framework + Segurança + Lakebase

- [ ] **Teoria**: Partner Well-Architected Framework
  - Pilares: segurança, performance, confiabilidade
  - Checklist de boas práticas
- [x] **PROJETO**: Integração com Databricks Lakebase
  - Substituir acesso via SQL Warehouse pela conexão PostgreSQL direta ao Lakebase (`sara-lakebase-dbx-app`)
  - Conexão via `psycopg2` — sem cold start de warehouse, menor latência para cargas de app
  - Credenciais injetadas via env vars no app runtime (remove `WAREHOUSE_ID` hardcoded)
  - Auth: `DATABRICKS_TOKEN` (local) ou M2M OAuth via SDK (Apps runtime)
- [x] **PROJETO**: UX — Navegação por abas
  - App reestruturado em `st.tabs()` com 4 abas: Visão Geral, Pedidos, Clientes, Produtos & Logística
  - Sidebar com filtros persiste em todas as abas
  - `app.py` separado em módulos: `queries.py`, `charts.py`, `app.py`

**Recursos**:

- Partner Well-Architected Hub
- [Databricks Lakebase docs](https://docs.databricks.com/en/database/lakebase/)

### Dias 3-4: Testes + CI/CD + Lakebase integração completa

- [ ] **Teoria**: Revisar práticas de engenharia
  - Clean Code, SOLID para pipelines
  - Testing: unit, integration, data quality
- [x] **PROJETO**: Testes e CI/CD
  - 24 testes unitários em `tests/` (`test_queries.py`, `test_charts.py`)
  - `conftest.py` com mocks de streamlit, psycopg2 e databricks-sdk
  - `bitbucket-pipelines.yml`: lint + testes no PR, `bundle deploy` no merge
  - Padrão inspirado no `indicium-solution-nexus` (build validation antes do deploy)
- [x] **PROJETO**: Integração Lakebase end-to-end (Dia 3)
  - 4 tabelas TPC-H sincronizadas via `databricks postgres create-synced-table` (`orders`, `customer`, `lineitem`, `part`)
  - Fix 3-part naming → nomes não qualificados + `search_path=tpch` na conexão psycopg2
  - Auth migrada para `generate_database_credential` (token OAuth ~60 min, cache 45 min)
  - `deploy_preview.sh`: criação automática de role Lakebase para SP do app, schema único por PR, retry em app órfão de deploy parcial
- [x] **PROJETO**: CI desbloqueado + code review (Dia 4 — 2026-05-28)
  - Schemas stale removidos (`dev_mesh_dev_sp_dev_ana_cunha` e variantes) — CI `Deploy to dev` funcional
  - Code review `/code-review high` com Claude Code: 7 findings (2 bugs de dados, 1 crash, 1 SQL injection, 2 reliability, 1 performance)
  - Findings documentados em `docs/LESSONS_LEARNED.md` e `docs/CHANGELOG.md`

**Recursos**:

- [GitHub Databricks Labs](https://github.com/databrickslabs)
- Databricks Labs CI/CD templates

### Dia 5: Finalização + Apresentação

- [x] **PROJETO**: Finalizar e documentar
  - [x] Code review assistido por IA (durante desenvolvimento)
  - [x] README completo (features, estrutura, deploy, status)
  - [x] Atualizar `ARCHITECTURE.md` com decisões da Semana 2 (Lakebase, módulos, CI/CD)
  - [x] Branding Indicium AI aplicado (tema Streamlit, logo, Inter, paleta de charts)
  - [x] Charts: labels abreviados (Mi/Bi/k), Pedidos por Mês, tick dinâmico
  - [x] Fix CI: nome do app preview dentro do limite de 30 chars
  - [x] Documentação atualizada (CHANGELOG v2.2, ARCHITECTURE, LESSONS_LEARNED, ESTADO_ATUAL)
  - [x] Fix CSS: seletor de fonte Inter corrigido para não sobrescrever ícones do Streamlit (Material Icons)
  - [x] Screenshots da v2.2 adicionadas ao CHANGELOG
  - [ ] Demo de 15 min para a equipe (agendar)

**Recursos**:

- [Databricks CLI docs](https://docs.databricks.com/dev-tools/cli/)

---

## 🏗️ Arquitetura Utilizada

> Detalhes completos em [docs/ARCHITECTURE.md](databricks-dashboard-app/docs/ARCHITECTURE.md)

### Stack Utilizada

| Camada | Tecnologia | Notas |
| --- | --- | --- |
| Frontend | Streamlit 1.50+ | Filtros sidebar, cache por parâmetros, navegação por abas (`st.tabs`) |
| Visualização | Altair | Stacked bars, line chart, tooltips customizados |
| Backend | Databricks SDK `WorkspaceClient` | Statement Execution API (Delta Lake) |
| Dados (analítico) | Delta Lake `samples.tpch` (SF 10) | Colunas com prefixo TPC-H: `o_`, `c_`, `l_` |
| Dados (app) | Databricks Lakebase `sara-lakebase-dbx-app` | PostgreSQL-compatível, acesso via `psycopg2` |
| Auth | M2M OAuth via Service Principal | `CLIENT_ID` + `CLIENT_SECRET` injetados pelo Apps runtime |
| Deploy | DAB (Data Asset Bundles) | `bundles/dashboard-metrics/`, targets dev/prod |
| CI/CD | Bitbucket Pipelines | `databricks bundle deploy` automatizado no merge |
| Qualidade | Ruff + pre-commit | Python 3.12, Google style, line-length 120 |

### Decisões-chave

- `@st.cache_resource` para `WorkspaceClient` (evita nova conexão OAuth a cada re-run)
- `@st.cache_data(ttl=300)` para resultados de queries (5 min)
- Filtros passados como `tuple` (hashable) para serem cache key no `@st.cache_data`
- Warehouse ID hardcoded no `app.yaml` — limitação do sandbox sem permissão `MANAGE`

---

## 🤖 Claude & AI Tools Utilizados

### Claude Code (CLI + VSCode Extension)

Principal ferramenta de desenvolvimento utilizada em todas as sessões.

| Skill / Comando | Quando foi usado |
| --- | --- |
| Geração de código | Scaffold inicial, funções de query, componentes Streamlit |
| `/init` | Geração da documentação inicial (ARCHITECTURE.md, README) |
| `/review` | Code review assistido por IA antes de PRs |
| Debugging assistido | Diagnóstico de erros de deploy DAB, 403 no OBO token, cache key issues |
| Refactoring | Extração de constantes, reorganização de funções |

### MCP / Marketplace

Não utilizados até o momento. Atualizar caso alguma integração seja adicionada nas próximas sessões.

---

## 📦 Entregas Finais do Projeto

- [x] **Código**: Repositório Git estruturado (Bitbucket)
- [x] **Deploy**: App funcionando via DAB (`https://dev-dashboard-metrics-2591888035258875.aws.databricksapps.com`)
- [x] **Docs**: README + ARCHITECTURE.md + LESSONS_LEARNED.md
- [ ] **Apresentação**: Demo de 15 min para equipe (agendar)
- [x] **Retrospectiva**: [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md) — conexão, configuração e deploy

---

## 📊 Indicadores de Sucesso

Ao final das 2 semanas, você deve ser capaz de:

- [x] Criar e deployar Databricks App do zero
- [x] Usar DAB CLI com confiança (bundle, deploy, multi-ambiente)
- [ ] Aplicar boas práticas do Well-Architected Framework
- [x] Ter um projeto de referência completo e documentado
- [x] Usar Claude/plugins no workflow diário de desenvolvimento

---

## 📚 Recursos Principais

### Documentação Oficial

- **Databricks**: <https://docs.databricks.com>
- **Claude**: <https://docs.anthropic.com>
- **Delta Lake**: <https://docs.delta.io>
- **DAB**: <https://docs.databricks.com/en/dev-tools/bundles/>

---

## 📝 Notas

- Ajustar cronograma conforme demandas do R&D
- Compartilhar progresso com a liderança/equipe
- Ao final, agendar demo de 15 min do projeto (se possível)

---

**Criado em**: 2026-05-15  
**Última atualização**: 2026-05-28  
**Próxima revisão**: Final da Semana 2
