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

## Resumo dos Workarounds do Sandbox

| Limitação | Contorno aplicado |
| --- | --- |
| OBO token retorna 403 | M2M OAuth via `WorkspaceClient()` |
| Sem permissão `MANAGE` no warehouse | `WAREHOUSE_ID` hardcoded no `app.yaml` |
| `mode: development` + `permissions:` incompatíveis | Removido bloco `permissions:` dos targets dev/ci |
| `app.yaml` sem parametrização | Valores hardcoded por enquanto |
| SP sem acesso ao warehouse | `CAN_USE` concedido manualmente via UI |
