# Lições Aprendidas — Databricks App + DAB

Retrospectiva do primeiro app Databricks desenvolvido durante o plano de estudos (2026-05-18 a 2026-05-21).
Serve de referência para os próximos projetos no sandbox indimesh.

---

## Conexão

### Autenticação: OBO token não funciona no sandbox

**Problema**: O token do usuário logado (`X-Forwarded-Access-Token`) retorna `403 Forbidden` ao chamar a Statement Execution API (`/api/2.0/sql/statements/`) no sandbox indimesh.

**Causa**: Restrição de permissões do sandbox — o token OBO não tem escopo suficiente para o REST API de SQL.

**Solução**: Usar M2M OAuth via Service Principal com `WorkspaceClient()`. O SDK lê `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET` automaticamente quando injetados pelo Databricks Apps runtime.

```python
@st.cache_resource
def _client() -> WorkspaceClient:
    return WorkspaceClient()  # usa M2M OAuth automaticamente
```

**Impacto**: O app não opera no contexto do usuário logado — todas as queries rodam com as permissões do Service Principal da app.

---

### Cache de conexão é obrigatório no Streamlit

**Problema**: Sem cache, o Streamlit re-executa todo o script a cada interação do usuário, criando uma nova conexão OAuth + TCP a cada clique. Isso causa latência de 2-3 minutos.

**Solução**: `@st.cache_resource` para o `WorkspaceClient` (singleton por processo) e `@st.cache_data(ttl=300)` para resultados de queries (5 min de TTL).

**Detalhe importante**: Filtros passados como parâmetros para funções cacheadas devem ser `tuple`, não `list` — listas não são hashable e quebram o cache key.

```python
@st.cache_data(ttl=300)
def fetch_orders(segments: tuple[str, ...], start: date, end: date) -> pd.DataFrame:
    ...
```

---

### SDK vs. databricks-sql-connector

**Decisão**: Usar `w.statement_execution.execute_statement()` do Databricks SDK em vez de `databricks-sql-connector`.

**Motivo**: O SDK já gerencia autenticação M2M. Adicionar `databricks-sql-connector` seria dependência redundante para o mesmo resultado.

---

### Colunas do samples.tpch seguem padrão TPC-H

As colunas têm prefixo de tabela — não é `status`, é `o_orderstatus`; não é `name`, é `c_name`.

| Tabela | Exemplo de colunas |
| --- | --- |
| `orders` | `o_orderkey`, `o_totalprice`, `o_orderstatus`, `o_orderdate`, `o_custkey` |
| `customer` | `c_custkey`, `c_name`, `c_mktsegment` |
| `lineitem` | `l_orderkey`, `l_extendedprice`, `l_discount` |

---

## Configuração

### Token precisa de escopo `all-apis`

**Problema**: `bundle deploy` usa a Workspace Files API (`/api/2.0/workspace-files/import-file/`), que não aceita tokens com escopos específicos (`workspace`, `sql`, `access-management` — nenhum é suficiente).

**Solução**: Gerar o token em `~/.databrickscfg` com escopo `all-apis`.

---

### `mode: development` é incompatível com bloco `permissions:`

**Problema**: Ao usar `mode: development` em um target, o DAB rejeita qualquer bloco `permissions:` no mesmo target com erro de validação.

**Solução**: Remover o bloco `permissions:` dos targets `dev` e `ci`. Permissões são gerenciadas manualmente nesses ambientes.

```yaml
# targets.yml — targets dev/ci NÃO devem ter bloco permissions:
targets:
  dev:
    mode: development
    # permissions: <-- remover
```

---

### Resource binding de SQL warehouse exige permissão MANAGE

**Problema**: Configurar o warehouse via resource binding no bundle (`resources[].sql_warehouse`) exige que o usuário tenha permissão `MANAGE` no warehouse. No sandbox, essa permissão não está disponível.

**Solução**: Definir o `WAREHOUSE_ID` diretamente como variável de ambiente no `app.yaml`:

```yaml
# app.yaml
env:
  - name: WAREHOUSE_ID
    value: "7cf9ef9ac39256ad"
```

**Limitação**: O `app.yaml` ainda não suporta parametrização ([issue cli#3679](https://github.com/databricks/cli/issues/3679)), então o valor fica hardcoded por ambiente.

---

### Service Principal precisa de CAN_USE no warehouse

**Problema**: Mesmo com autenticação M2M configurada, as queries retornam `PermissionDenied` se o Service Principal da app não tiver permissão no warehouse.

**Solução**: Conceder `CAN_USE` ao SP via UI (Compute → SQL Warehouses → Permissions) ou via CLI:

```bash
databricks warehouses set-permissions <warehouse-id> \
  --access-control service_principal_name=<sp-name>,permission_level=CAN_USE
```

O SP da app neste projeto: `7a5205b1-aecc-4755-bde4-dea31c487ed7`

---

## Deploy

### Sequência correta de primeiro deploy

```bash
cd bundles/dashboard-metrics

# 1. Deploy dos recursos (cria a app no workspace)
databricks bundle deploy --target dev

# 2. Inicia a app (necessário na primeira vez)
databricks apps start <app-name>

# 3. Deploy do código-fonte
databricks apps deploy <app-name> \
  --source-code-path /Workspace/Users/<user>/.bundle/<bundle>/dev/files/src/app
```

**Atenção**: `--source-code-path` exige o path no workspace (começando com `/Workspace/`), não o path local.

---

### Redeployar app com mesmo nome

Se a app já existe e você precisa recriar do zero:

```bash
databricks apps delete <app-name>
# aguardar conclusão (verificar com: databricks apps get <app-name>)
databricks bundle deploy --target dev
databricks apps start <app-name>
```

Não tente redeployar enquanto a app anterior ainda existe com mesmo nome — causa conflito.

---

### bundle deploy usa Workspace Files API

O `bundle deploy` faz upload dos arquivos via `/api/2.0/workspace-files/import-file/`, que é diferente da Files API (`/api/2.0/fs/files/`). Isso explica por que o escopo `all-apis` é necessário — escopos específicos não cobrem essa endpoint.

---

## Lakebase (Semana 2)

### Sincronizando dados do Unity Catalog para o Lakebase

O Lakebase é um banco PostgreSQL gerenciado. Ele não lê tabelas Delta do Unity Catalog diretamente — é preciso criar uma **synced table** (pipeline DLT) para cada tabela que a app vai consumir.

**Comando**:

```bash
databricks postgres create-synced-table "<catalog>.<schema>.<table>" \
  --parent "projects/<project>" \
  --json '{
    "spec": {
      "source_delta_table": "samples.tpch.<table>",
      "scheduling_policy": "TRIGGERED",
      "primary_key_columns": ["<pk_col>"]
    }
  }'
```

**Restrições importantes**:

- O synced table ID (primeiro argumento) deve estar em um **catálogo gerenciado** — `samples` não é permitido. Usar `mesh_dev_db.tpch.<table>`.
- O schema destino (`mesh_dev_db.tpch`) deve existir antes: `databricks schemas create tpch mesh_dev_db`.
- `scheduling_policy` é obrigatório (use `"TRIGGERED"` para sync manual ou `"CONTINUOUS"` para streaming).
- `primary_key_columns` é obrigatório mesmo que a tabela Delta não tenha PK definida.

**Tabelas TPC-H sincronizadas** (projeto `sara-lakebase-dbx-app`, branch `production`):

| Tabela | Linhas | PK |
| --- | --- | --- |
| `orders` | 7.5M | `o_orderkey` |
| `customer` | 750K | `c_custkey` |
| `lineitem` | 30M | `l_orderkey, l_linenumber` |
| `part` | 1M | `p_partkey` |

---

### Lakebase não suporta nomes 3-partes (catalog.schema.table)

**Problema**: Queries com `samples.tpch.orders` no Lakebase retornam `cross-database references are not implemented`. O Postgres interpreta o primeiro segmento como um banco de dados, não um catálogo Unity Catalog.

**Solução**: Usar nomes de tabela sem qualificação e definir `search_path` na string de conexão:

```python
# queries.py — nomes sem catálogo/schema
_T_ORDERS   = "orders"
_T_CUSTOMER = "customer"

# _connect() — search_path define o schema padrão
psycopg2.connect(
    ...
    options=f"-c search_path={SCHEMA}",  # SCHEMA = "tpch"
)
```

---

### Autenticação no Lakebase via `generate_database_credential`

**Problema**: O método `_workspace_client().config.authenticate()` não gera credenciais OAuth para Lakebase — ele gera headers HTTP para a Workspace API, não tokens Postgres.

**Solução**: Usar `generate_database_credential` do SDK, que emite tokens OAuth de curta duração (~60 min) específicos para o endpoint Lakebase:

```python
@st.cache_data(ttl=2700)  # 45 min — tokens duram ~60 min
def _get_token(endpoint: str) -> str:
    cred = _workspace_client().postgres.generate_database_credential(endpoint=endpoint)
    return cred.token
```

O `endpoint` é o resource path: `projects/<project>/branches/<branch>/endpoints/<endpoint-id>`.

---

### `role_id` do Lakebase deve começar com letra

**Problema**: UUIDs de Service Principals começam com dígito (ex: `7a5205b1-...`). O campo `role_id` da API `create-role` exige o padrão `^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$`.

**Solução**: Prefixar com `sp-`. O campo `postgres_role` (username real no Postgres) continua como o UUID sem prefixo:

```bash
databricks postgres create-role "${BRANCH_RESOURCE}" \
  --role-id "sp-${APP_SP}" \
  --json "{\"spec\": {
    \"identity_type\": \"SERVICE_PRINCIPAL\",
    \"postgres_role\": \"${APP_SP}\",
    \"auth_method\": \"LAKEBASE_OAUTH_V1\",
    \"membership_roles\": [\"DATABRICKS_SUPERUSER\"]
  }}"
```

---

### `databricks bundle run` vs `apps start`

**Problema**: `databricks apps start` apenas ativa a app — não faz deploy do código. Para implantar nova versão do código via DAB, o correto é `bundle run`.

**Solução**: Após `bundle deploy`, usar `bundle run <resource_key>` para iniciar/atualizar a app com o código novo:

```bash
databricks bundle deploy --target preview --var "pr_id=${PR_ID}"
databricks bundle run dashboard_metrics_app --target preview --var "pr_id=${PR_ID}"
```

---

### `apps set-permissions` vs `apps permissions set`

O subcomando correto para definir permissões de apps via CLI é `set-permissions`, não `permissions set`:

```bash
# Correto:
databricks apps set-permissions "${APP_NAME}" \
  --json '{"access_control_list": [...]}'

# Errado (retorna "unknown command"):
databricks apps permissions set "${APP_NAME}" ...
```

---

## Resumo dos Workarounds do Sandbox

| Limitação | Contorno aplicado |
| --- | --- |
| OBO token retorna 403 | M2M OAuth via `WorkspaceClient()` |
| Sem permissão `MANAGE` no warehouse | `WAREHOUSE_ID` hardcoded no `app.yaml` |
| `mode: development` + `permissions:` incompatíveis | Removido bloco `permissions:` dos targets dev/ci |
| `app.yaml` sem parametrização | Valores hardcoded por enquanto |
| SP sem acesso ao warehouse | `CAN_USE` concedido manualmente via UI |
| Lakebase não aceita nomes 3-partes | Nomes de tabela sem qualificação + `search_path` na conexão |
| `samples` não permite synced tables | Synced tables criadas em `mesh_dev_db.tpch` |
| `role_id` não pode começar com dígito | Prefixo `sp-` no role_id; UUID mantido no `postgres_role` |
