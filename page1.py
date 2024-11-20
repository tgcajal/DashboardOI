"""Page 1"""


import streamlit as st 
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime 
from datetime import date, timedelta 
import pdftest as pdf

from processing import prep_pipeline
import reportes_funciones as rf

st.title('Análisis de Cartera')

#######################################
# DATA LOADING
#######################################
today = datetime.datetime.today()

column_config_dinero={
        "name": 
        "appname",
        "index": st.column_config.TextColumn(
            "",
        ),
        "Monto (USD)": st.column_config.NumberColumn(
            "Monto (USD)",
            format="$ %.2f",
        ),
        "Porcentaje": st.column_config.NumberColumn(
            "Porcentaje",
            format="%.2f %%",
        ),
    }

column_config_cantidad={
        "name": "appname",
        "index": st.column_config.TextColumn(
            "",
        ),
        "Cantidad": st.column_config.NumberColumn(
            "Cantidad",
            format="%.0f",
        ),
        "Porcentaje": st.column_config.NumberColumn(
            "Porcentaje",
            format="%.2f %%",
        ),
    }

@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    return df

@st.cache_data
def clean_data(df, start_date=False, end_date=False, pais=st.session_state.pais):
    df = rf.clean(df, start_date, end_date, pais)
    return df

original_df = load_data('cashflow.csv')

if "df" not in st.session_state:
    st.session_state.df = clean_data(original_df)

if "pais" not in st.session_state:
        st.session_state.pais = ['El Salvador','Honduras']


tablas = [('Indicadores de Cartera Total (Pendiente)',rf.indicadores_cartera_pendiente(rf.clean(original_df))),
        ('Créditos Otorgados',rf.indicadores_creditos_otorgados(st.session_state.df)),
        ('Montos',rf.indicadores_montos(rt.clean(df, pais=st.session_state.pais)),
        ('Mora vs Saldo Actual',rf.indicadores_mora_saldo(st.session_state.df)),
        ('Mora Contagiada vs Saldo Actual',rf.indicadores_mora_saldo(st.session_state.df, c=True)),
        ('Créditos en Mora vs Créditos Activos',rf.indicadores_mora_creditos(st.session_state.df))]

@st.cache_resource
def generate_report():
    file = pdf.create_pdf_report(tablas, "analisis_cartera.pdf")
    return file

report = generate_report()

with open("analisis_cartera.pdf", "rb") as file:
    btn = st.download_button(
        label="Descargar PDF",
        data=file,
        file_name="analisis_cartera.pdf",
        mime="application/pdf"
    )


# Indicadores
st.header(tablas[0][0])
st.dataframe(tablas[0][1], column_config=column_config_dinero, hide_index=True)

# Creditos
st.header(tablas[1][0])
st.dataframe(tablas[1][1], column_config=column_config_cantidad, hide_index=True)

# Montos
#st.header(tablas[2][0])
#st.dataframe(tablas[2][1], hide_index=True)

# Mora vs saldo
st.header(tablas[3][0])
st.dataframe(tablas[3][1], column_config=column_config_dinero, hide_index=True)

# Mora contagiada vs saldo
st.header(tablas[4][0])
st.dataframe(tablas[4][1], column_config=column_config_dinero, hide_index=True)

# Creditos mora vs activos
st.header(tablas[5][0])
st.dataframe(tablas[5][1], column_config=column_config_cantidad, hide_index=True)
