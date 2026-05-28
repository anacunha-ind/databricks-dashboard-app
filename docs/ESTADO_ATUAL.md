# Documentação — Dashboard de Métricas

Este diretório centraliza a documentação técnica e de processo do projeto [`databricks-dashboard-app`](../README.md).

---

## Índice de Documentos

### [ARCHITECTURE.md](ARCHITECTURE.md)

Descreve as decisões arquiteturais do projeto, organizadas por área. Atualizado ao final de cada semana de desenvolvimento para refletir mudanças de design.

**Conteúdo:**

- Visão geral do sistema e stack tecnológica
- Estrutura de diretórios e responsabilidade de cada módulo
- Padrões de código (Python 3.12, Google style, Ruff)
- Decisões arquiteturais com justificativa:
  - Autenticação M2M OAuth via Service Principal
  - Migração da Statement Execution API para Lakebase via psycopg2
  - Separação em módulos (`queries.py`, `charts.py`, `app.py`)
  - Cache de conexão e dados com `@st.cache_resource` / `@st.cache_data`
  - Nomes de tabela não qualificados + `search_path` na conexão (Lakebase não suporta 3-part naming)
  - CI/CD com Bitbucket Pipelines
- Limitações conhecidas do sandbox e contornos aplicados
- Histórico de status por semana

**Quando consultar**: ao revisar uma decisão de design, entender por que algo foi implementado de determinada forma, ou ao integrar um novo membro ao projeto.

---

### [LESSONS_LEARNED.md](LESSONS_LEARNED.md)

Retrospectiva técnica dos principais problemas encontrados e resolvidos durante o desenvolvimento. Serve de referência para futuros projetos no sandbox indimesh.

**Conteúdo:**

- **Conexão**: OBO token retorna 403 no sandbox; solução via M2M OAuth. Cache obrigatório no Streamlit. Convenção de colunas TPC-H. Lakebase não suporta 3-part naming — nomes não qualificados + `search_path`. Auth OAuth via `generate_database_credential`.
- **Configuração**: Token `all-apis` obrigatório para `bundle deploy`. `mode: development` incompatível com `permissions:`. Resource binding de warehouse exige `MANAGE`. Schema único por PR no target preview para evitar colisão com target dev.
- **Deploy**: Sequência correta (bundle deploy → bundle run). `apps set-permissions` (não `permissions set`). Retry automático em app órfão de deploy parcial. Role Lakebase para SP do app com prefixo `sp-`.

**Quando consultar**: antes de iniciar um novo projeto no mesmo sandbox, ou ao depurar erros de autenticação e deploy que não estão na documentação oficial.

---

### [CHANGELOG.md](CHANGELOG.md)

Histórico de versões com capturas de tela do dashboard em cada etapa do desenvolvimento.

**Conteúdo:**

- v2.2 (2026-05-28): branding Indicium AI, melhorias de charts (Mi/Bi, labels, Pedidos por Mês), fix nome app preview, fix CSS ícones sidebar, screenshots das 4 abas
- v2.1 (2026-05-28): CI desbloqueado, code review com 7 findings documentados
- v2.0 (2026-05-27): migração para Lakebase, 4 abas, CI/CD por PR, com screenshots das 4 abas
- v1.0 (2026-05-18): primeira versão funcional com Delta Lake, página única

**Quando consultar**: para ver a evolução visual do produto ou comparar o antes/depois de uma migração técnica.

---

### [STUDY_PLAN.md](STUDY_PLAN.md)

Plano de estudos de 2 semanas em Databricks Apps & Software Engineering, com checkboxes de progresso e links para recursos consultados.

**Conteúdo:**

- Especificação do projeto prático construído durante os estudos
- Cronograma por dia com tarefas teóricas e práticas
- Stack utilizada e decisões-chave por semana
- Registro de uso de Claude Code e AI tooling
- Indicadores de sucesso e entregas finais

**Quando consultar**: para acompanhar o progresso do plano de estudos ou como referência de estrutura para futuros planos similares.

---

### [images/](images/)

Screenshots do dashboard em diferentes fases de desenvolvimento.

| Arquivo | Conteúdo |
| --- | --- |
| `dashboard_dia3.png` | Dashboard ao final da Semana 1 — KPIs, charts Altair, filtros por sidebar |
| `dashboards.png` | Visão geral das abas do dashboard (Semana 2) |

---

## Documentação no Repositório

Além dos arquivos neste diretório, os documentos abaixo na raiz do repositório fazem parte da documentação do projeto:

| Arquivo | Descrição |
| --- | --- |
| [`README.md`](../README.md) | Visão geral do projeto, setup local, instruções de deploy e status atual |
| [`bitbucket-pipelines.yml`](../bitbucket-pipelines.yml) | Definição do pipeline CI/CD — lint + testes no PR, `bundle deploy` no merge para `main` |
| [`pyproject.toml`](../pyproject.toml) | Configuração de Ruff (linter) e pytest — regras de qualidade de código aplicadas no pipeline |

---

## Histórico de Atualizações

| Data | Documento | O que mudou |
| --- | --- | --- |
| 2026-05-18 | `ARCHITECTURE.md`, `LESSONS_LEARNED.md` | Criação inicial — Semana 1 (setup, Statement Execution API, deploy DAB) |
| 2026-05-25 | `ARCHITECTURE.md`, `STUDY_PLAN.md` | Atualização Semana 2 — Lakebase via psycopg2, módulos, testes, CI/CD Bitbucket Pipelines |
| 2026-05-25 | `docs/README.md` | Criação deste índice descritivo |
| 2026-05-27 | `CHANGELOG.md` | Criação — histórico de versões com screenshots |
| 2026-05-27 | `ARCHITECTURE.md`, `STUDY_PLAN.md` | Semana 2 Dia 3 — Lakebase, search_path, generate_database_credential, deploy preview |
| 2026-05-28 | `CHANGELOG.md`, `ARCHITECTURE.md`, `LESSONS_LEARNED.md`, `README.md` | Semana 2 Dia 5 — branding Indicium AI, melhorias de charts, fix app name limit |
