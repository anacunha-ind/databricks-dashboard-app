# Arquitetura do Dashboard de Métricas

## Visão Geral

Dashboard de métricas desenvolvido como Databricks App utilizando Streamlit para visualização de dados provenientes do Delta Lake.

## Stack Tecnológica

### Frontend
- **Streamlit 1.50+**: Framework Python para dashboards interativos
- **Databricks SQL Connector**: Conexão com warehouse SQL

### Backend
- **Delta Lake**: Armazenamento de dados
- **Databricks SQL Warehouse**: Engine de processamento

### Deploy
- **DAB (Data Asset Bundles)**: Deploy automatizado
- **Ambientes**: dev + prod

## Estrutura do Projeto

```
databricks-dashboard-app/
├── app/
│   └── main.py                 # Aplicação Streamlit principal
├── databricks/
│   └── databricks.yml          # Configuração DAB
├── tests/                      # Testes automatizados (futuro)
├── docs/                       # Documentação
├── app.yaml                    # Configuração de runtime
├── requirements.txt            # Dependências Python
├── pyproject.toml              # Configuração do projeto
└── README.md                   # Documentação principal
```

## Padrões de Código

### Python
- **Versão**: Python 3.12
- **Style Guide**: Google Python Style Guide
- **Docstrings**: Google format
- **Linter**: Ruff (line-length: 120)
- **Type Hints**: Obrigatório em funções públicas

### Organização
- Funções utilitárias com `@st.cache_resource` para performance
- Separação clara entre lógica de negócio e apresentação
- Conexões persistentes para evitar connection exhaustion

## Decisões Arquiteturais

### Conexão com Databricks
**Decisão**: Usar `@st.cache_resource` para conexões SQL

**Justificativa**: Streamlit re-executa todo o script a cada interação. Sem cache, cada re-run cria nova conexão TCP + OAuth negotiation, causando exhaustion e freezes de 2-3 minutos.

**Referência**: [Databricks Apps - Other Frameworks Guide](https://docs.databricks.com/en/dev-tools/databricks-apps/)

### Configuração de Porta e Host
**Decisão**: Usar `DATABRICKS_APP_PORT` environment variable e bind em `0.0.0.0`

**Justificativa**: Databricks Apps platform atribui porta dinamicamente. Hardcoding ou bind em localhost causa 502 Bad Gateway.

### CORS e XSRF
**Decisão**: Desabilitar CORS e XSRF protection no Streamlit

**Justificativa**: O reverse proxy da Databricks usa origem diferente (`*.databricksapps.com` vs workspace origin), acionando proteção do Streamlit. Desabilitar é o workaround oficial.

## Próximos Passos

### Semana 1
- [x] Dia 1: Setup e estrutura inicial
- [ ] Dias 2-3: Conexão com Delta Lake + primeiro protótipo
- [ ] Dias 4-5: Empacotamento com DAB + deploy automatizado

### Semana 2
- [ ] Dias 1-2: Aplicar Well-Architected Framework
- [ ] Dias 3-4: Testes e refactoring
- [ ] Dia 5: Documentação final e apresentação

## Referências

- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/)
- [DAB Documentation](https://docs.databricks.com/en/dev-tools/bundles/)
- [Streamlit Documentation](https://docs.streamlit.io/)
