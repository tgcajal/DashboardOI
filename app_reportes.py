"""APP REPORTES"""

import streamlit as st 
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime 
from datetime import date, timedelta 
import pdftest as pdf

#######################################
# PAGE SETUP
#######################################

st.set_page_config(page_title="Reportes", page_icon=":bar_chart:", layout="wide")


import security

from processing import prep_pipeline
import reportes_funciones as rf

#######################################
# DATA LOADING
#######################################
today = datetime.datetime.today()

# column_config_dinero={
#         "name": 
#         "appname",
#         "index": st.column_config.TextColumn(
#             "",
#         ),
#         "Monto (USD)": st.column_config.NumberColumn(
#             "Monto (USD)",
#             format="$ %.2f",
#         ),
#         "Porcentaje": st.column_config.NumberColumn(
#             "Porcentaje",
#             format="%.2f %%",
#         ),
#     }

# column_config_cantidad={
#         "name": "appname",
#         "index": st.column_config.TextColumn(
#             "",
#         ),
#         "Cantidad": st.column_config.NumberColumn(
#             "Cantidad",
#             format="%.0f",
#         ),
#         "Porcentaje": st.column_config.NumberColumn(
#             "Porcentaje",
#             format="%.2f %%",
#         ),
#     }

# @st.cache_data
# def load_data(path: str):
#     df = pd.read_csv(path)
#     return df

# @st.cache_data
# def clean_data(df, start_date=False, end_date=False, pais=False):
#     df = rf.clean(df, start_date, end_date, pais)
#     return df

# original_df = load_data('cashflow.csv')

# if "df" not in st.session_state:
#     st.session_state.df = clean_data(original_df)


# Filters
# def page1():

#     tablas = [('Indicadores de Cartera Total (Pendiente)',rf.indicadores_cartera_pendiente(st.session_state.df)),
#             ('Créditos Otorgados',rf.indicadores_creditos_otorgados(st.session_state.df)),
#             ('Montos',rf.indicadores_montos(st.session_state.df)),
#             ('Mora vs Saldo Actual',rf.indicadores_mora_saldo(st.session_state.df)),
#             ('Mora Contagiada vs Saldo Actual',rf.indicadores_mora_saldo(st.session_state.df, c=True)),
#             ('Créditos en Mora vs Créditos Activos',rf.indicadores_mora_creditos(st.session_state.df))]

#     @st.cache_resource
#     def generate_report():
#         file = pdf.create_pdf_report(tablas, "your_file.pdf")
#         return file

#     report = generate_report()

#     with open("your_file.pdf", "rb") as file:
#         btn = st.download_button(
#             label="Download PDF",
#             data=file,
#             file_name="downloaded_file.pdf",
#             mime="application/pdf"
#         )


#     # Indicadores
#     st.header(tablas[0][0])
#     st.dataframe(tablas[0][1], column_config=column_config_dinero, hide_index=True)

#     # Creditos
#     st.header(tablas[1][0])
#     st.dataframe(tablas[1][1], column_config=column_config_cantidad, hide_index=True)

#     # Montos
#     st.header(tablas[2][0])
#     st.dataframe(tablas[2][1], hide_index=True)

#     # Mora vs saldo
#     st.header(tablas[3][0])
#     st.dataframe(tablas[3][1], column_config=column_config_dinero, hide_index=True)

#     # Mora contagiada vs saldo
#     st.header(tablas[4][0])
#     st.dataframe(tablas[4][1], column_config=column_config_dinero, hide_index=True)

#     # Creditos mora vs activos
#     st.header(tablas[5][0])
#     st.dataframe(tablas[5][1], column_config=column_config_cantidad, hide_index=True)

# def page2():
#     st.write("WIP")
#     st.write(st.session_state.pais)

#     tablas = [('Análisis de Cosecha',rf.analisis_cosecha(st.session_state.df)),
#             ('Mora - Monto',rf.mora_monto(st.session_state.df)),
#             ('Mora vs Saldo Actual',rf.mora_saldo(st.session_state.df)),
#             ('Mora Contagiada - Monto',rf.mora_monto(st.session_state.df, c=True)),
#             ('Mora Contagiada vs Saldo Actual',rf.mora_saldo(st.session_state.df, c=True)),
#             ('Créditos en Mora vs Créditos Activos',rf.indicadores_mora_creditos(st.session_state.df))]

#     @st.cache_resource
#     def generate_report():
#         file = pdf.create_pdf_report(tablas, "your_file.pdf")
#         return file

#     #report = generate_report()

#     with open("your_file.pdf", "rb") as file:
#         btn = st.download_button(
#             label="Download PDF",
#             data=file,
#             file_name="downloaded_file.pdf",
#             mime="application/pdf"
#         )
    
#     # Analisis cosecha
#     st.header(tablas[0][0])
#     st.dataframe(tablas[0][1], hide_index=True)

#     # Mora - Monto
#     st.header(tablas[1][0])
#     st.dataframe(tablas[1][1], column_config=column_config_dinero)

#     # Mora vs saldo actual
#     st.header(tablas[2][0])
#     st.dataframe(tablas[2][1], column_config=column_config_cantidad)

#     # Mora contagiada monto
#     st.header(tablas[3][0])
#     st.dataframe(tablas[3][1], column_config=column_config_dinero)

#     # Mora contagiada vs saldo
#     st.header(tablas[4][0])
#     st.dataframe(tablas[4][1], column_config=column_config_cantidad)

    

# st.sidebar.write('Ver por quincena')
# st.sidebar.toggle('Quincena',key='frecuencia')
st.sidebar.multiselect("País",['El Salvador','Honduras'], key='pais')
# st.sidebar.selectbox("Frecuencia",['Mensual','Quincenal'])
# st.sidebar.write('Filtrar por período:')
# st.sidebar.date_input(label='Seleccionar fechas', value=(datetime.date(2024,8,1), today), min_value=datetime.date(2024,8,1), max_value=today, key='date_range')

# def aplicar_callback():
#     st.session_state.df = clean_data(original_df, start_date=st.session_state.date_range[0], end_date=st.session_state.date_range[1], pais=st.session_state.pais)
# st.sidebar.button(label='Aplicar', on_click=aplicar_callback, type='primary')


pg = st.navigation([st.Page('page1.py', title='Análisis de Cartera'), st.Page('page2.py', title='Análisis de Cosecha')])
pg.run()
