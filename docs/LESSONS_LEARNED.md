# Lições Aprendidas — Databricks App + DAB

Retrospectiva do primeiro app Databricks desenvolvido durante o plano de estudos (2026-05-18 a 2026-05-27).
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

## Ambientes de Preview por PR (Semana 2, Dia 2 — 2026-05-27)

Implementação de ambientes efêmeros por PR: cada Pull Request gera um Databricks App isolado (`preview-pr-N-dashboard-metrics`) com um branch Lakebase próprio (copy-on-write a partir de `production`). Os principais aprendizados:

### Cada Databricks App ganha um Service Principal próprio

**Problema**: O app de preview falhava com `password authentication failed for user '<uuid>'` ao conectar no Lakebase. O UUID não era o SP de deploy (`mesh-dev-sp`), mas um SP novo.

**Causa**: O Databricks Apps cria automaticamente um Service Principal dedicado por app. O `preview-pr-5` rodava como `aa867ae5-...`, diferente do SP de deploy.

**Impacto**: O SP do app precisa existir como **role no Postgres do branch Lakebase** — não basta ter token OAuth válido.

---

### Role do SP no Lakebase é auto-criada com `NO_LOGIN`

**Problema**: A role do SP do app existia no branch (`databricks postgres list-roles`), mas com `auth_method: NO_LOGIN` e `identity_type: IDENTITY_TYPE_UNSPECIFIED` — sem permissão de login.

**Solução**: Deletar a role quebrada e recriar com OAuth habilitado:

```bash
databricks postgres delete-role "projects/<proj>/branches/pr-N/roles/<role-id>"

databricks postgres create-role "projects/<proj>/branches/pr-N" \
  --role-id "preview-pr-N-sp" \
  --json '{"spec": {"identity_type": "SERVICE_PRINCIPAL", "postgres_role": "<app-sp-client-id>", "auth_method": "LAKEBASE_OAUTH_V1", "membership_roles": ["DATABRICKS_SUPERUSER"]}}'
```

**Atenção**: `update-role` não aceita alterar `auth_method`/`membership_roles` (campos read-only no update_mask) — por isso o padrão delete + create.

---

### `bundle deploy` NÃO publica o código do app — use `bundle run`

**Problema**: Após `bundle deploy --target preview`, o app subia com compute `ACTIVE` mas status `UNAVAILABLE` ("App has not been deployed yet"). `databricks apps list-deployments` retornava vazio.

**Causa**: Para recursos `apps`, o `bundle deploy` cria o recurso via Terraform e faz upload dos arquivos, mas **não cria um deployment** (o push efetivo do código para o app rodando). São operações separadas.

**Solução**: Adicionar `bundle run` após o `bundle deploy` — ele publica o código e inicia o app:

```bash
databricks bundle deploy --target preview --var "pr_id=${PR_ID}"
databricks bundle run   --target preview --var "pr_id=${PR_ID}" dashboard_metrics_app
```

---

### Branch Lakebase precisa de schema único por PR

**Problema**: `bundle deploy --target preview` falhava com `cannot create schema: Schema 'dev_mesh_dev_sp_dev_ana_cunha' already exists`.

**Causa**: Os targets `dev` e `preview` usavam o mesmo `dev_app_schema_name`. Com `mode: development`, o DAB gera o mesmo nome de schema (prefixado pelo SP), causando colisão.

**Solução**: Schema parametrizado por PR no target preview — `app_schema_name: preview_pr_${var.pr_id}`.

---

### Permissão de acesso ao app de preview

**Problema**: O usuário (mesmo quem abriu o PR) via "Permission Required" ao acessar o app. O app é criado pelo SP de deploy, então o usuário não herda acesso.

**Solução**: Conceder `CAN_USE` ao grupo `users` automaticamente no pipeline, logo após o `bundle run`:

```bash
databricks apps set-permissions "${APP_NAME}" \
  --json '{"access_control_list": [{"group_name": "users", "permission_level": "CAN_USE"}]}'
```

**Atenção**: o subcomando é `set-permissions` (não `permissions set`). E só o SP que criou o app (ou um admin) pode alterar permissões — o usuário comum recebe `apps.ruleSets/get` denied.

---

### Lakebase está vazio — dados nunca foram ingeridos (BLOQUEIO ATUAL)

**Problema**: Com auth resolvida, o app passou a falhar com `cross-database references are not implemented: "samples.tpch.orders"`.

**Causa**: As queries usam naming de 3 partes do Unity Catalog (`samples.tpch.orders`), mas o Lakebase é PostgreSQL puro — interpreta `samples` como um *database* separado. Inspecionando os branches `production` e `pr-5` via psycopg2, **ambos estão vazios** (só schemas de sistema + `public`). Os dados `samples.tpch` nunca foram sincronizados para o Lakebase.

**Próximo passo**: sincronizar as tabelas do UC para o Postgres do Lakebase (via `databricks postgres create-synced-table` ou ETL nos moldes do `populate-lakebase.sh` do solution-nexus) e ajustar as queries para naming de 2 partes (`schema.table`).

---

## Resumo dos Workarounds do Sandbox

| Limitação | Contorno aplicado |
| --- | --- |
| OBO token retorna 403 | M2M OAuth via `WorkspaceClient()` |
| Sem permissão `MANAGE` no warehouse | `WAREHOUSE_ID` hardcoded no `app.yaml` |
| `mode: development` + `permissions:` incompatíveis | Removido bloco `permissions:` dos targets dev/ci |
| `app.yaml` sem parametrização | Valores hardcoded por enquanto |
| SP sem acesso ao warehouse | `CAN_USE` concedido manualmente via UI |
| SP do app de preview sem role no Lakebase | `create-role` com `LAKEBASE_OAUTH_V1` por PR |
| `bundle deploy` não publica código de app | `bundle run` após o deploy |
| Schema colide entre dev e preview | `app_schema_name: preview_pr_${var.pr_id}` |
| Usuário sem acesso ao app de preview | `set-permissions` `CAN_USE` ao grupo `users` no pipeline |
