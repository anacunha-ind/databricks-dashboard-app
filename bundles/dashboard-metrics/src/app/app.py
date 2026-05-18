"""Dashboard de Métricas - Databricks App.

Aplicação Streamlit para visualização de métricas do Delta Lake.
Segue padrões de código da Indicium (Google docstrings, Ruff linting).
"""

import os

import streamlit as st
from databricks.sdk import WorkspaceClient

# Get configuration from environment variables
CATALOG_NAME = os.getenv("CATALOG_NAME", "mesh_dev_db")
SCHEMA_NAME = os.getenv("SCHEMA_NAME", "dev_dashboard")
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID")

# Validate required env vars
if not WAREHOUSE_ID:
    st.error("WAREHOUSE_ID environment variable is required.")
    st.stop()


@st.cache_resource
def get_client() -> WorkspaceClient:
    """Get cached Databricks WorkspaceClient.

    Uses @st.cache_resource to maintain persistent client and avoid
    connection exhaustion during Streamlit re-runs.

    Returns:
        WorkspaceClient: Databricks SDK client.
    """
    return WorkspaceClient()


def main():
    """Main application entry point."""
    # Configuração da página
    st.set_page_config(
        page_title="Dashboard de Métricas",
        page_icon="📊",
        layout="wide",
    )

    # Header
    st.title("📊 Dashboard de Métricas")
    st.markdown("*Powered by Databricks Apps & Delta Lake*")

    # Placeholder para desenvolvimento futuro
    st.info("🚧 Aplicação em desenvolvimento - Semana 1, Dia 1")

    # Seções do dashboard (estrutura inicial)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Total de Registros", value="0", delta="0")

    with col2:
        st.metric(label="Pipelines Ativos", value="0", delta="0")

    with col3:
        st.metric(label="Última Atualização", value="-", delta="-")

    # Seção de detalhes (placeholder)
    st.markdown("---")
    st.subheader("Detalhes")

    with st.expander("ℹ️ Sobre o Projeto"):
        st.markdown(
            """
            **Dashboard de Métricas** é um projeto hands-on do plano de estudos
            de Databricks Apps & Software Engineering.

            **Stack:**
            - Frontend: Streamlit
            - Backend: Delta Lake + Databricks SQL
            - Deploy: DAB (Data Asset Bundles)
            - Ambientes: dev + prod
            """
        )

    # Footer
    st.markdown("---")
    st.markdown("**Projeto**: Plano de Estudos Databricks Apps | **Data**: 2026-05-18")


if __name__ == "__main__":
    main()
