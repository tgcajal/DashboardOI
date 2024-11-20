"""Análisis de Cosecha"""

import streamlit as st 
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime 
from datetime import date, timedelta 
import pdftest as pdf
import reportes_funciones as rf

st.title('Análisis de Cosecha')

def clean(df, start_date=None, end_date=None, pais=None):

    df = df[~df['nombre_empresa'].isin(['(ANTERIOR) INVERSIONES EBEN EZER', 'GALO CELL', 'INVERSIONES EBEN EZER'])]
    
    df['fecha_cuota'] = pd.to_datetime(df['fecha_cuota'])
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])

    df['cuota_date'] = df['fecha_cuota'].dt.date

    today = datetime.date.today()
    df['dias_atraso_cuota'] = [today-fecha for fecha in df['cuota_date']]
    df['dias_atraso_cuota'] = df['dias_atraso_cuota']/ pd.Timedelta(days=1)
    df['dias_atraso_cuota'] = df['dias_atraso_cuota'].astype(int)

    df['saldo_actual'] = df['saldo_actual'].where(df['pais']=='El Salvador', df['saldo_actual']/25)
    df['valor_financiamiento'] = df['valor_financiamiento'].where(df['pais']=='El Salvador', df['valor_financiamiento']/25)

    estado_mora = {'Mora 15':range(1,30),
                'Mora 30':range(30,45),
                'Mora 45':range(45,60),
                'Mora 60':range(60,120)}

    df['estado_mora'] = None

    for index in df['dias_atraso'].index:
        for key in estado_mora:
            value = df['dias_atraso'][index]
            if value in estado_mora[key]:
                df.at[index,'estado_mora'] = key
    
    return df



# Analiss cosecha
def analisis_cosecha(df, frecuencia='M'):
    cosecha = df.set_index('fecha_venta').resample(frecuencia).agg({'id_credito':'nunique', #creditos otorgados
                                                          'fecha_cuota':'max', # dias fin sin procesar
                                                              })
    cosecha.rename(columns={'id_credito':'Créditos otorgados'}, inplace=True)#'fecha_cuota':'Fecha fin'}, inplace=True)
    #cosecha['Días fin de cosecha'] = today - cosecha['Fecha fin']
    cosecha['Cartera Total (Capital Pendiente)'] = df[df['estado'].isin(['Vencido','Exigible','Fijo'])].set_index('fecha_venta').resample(frecuencia).agg({'monto_cuota':'sum'})['monto_cuota']
    #cosecha['Cartera Total (Capital Pendiente)'] = df[df['estado']=='Fijo'].set_index('fecha_venta').resample('M').agg({'monto_cuota':'sum'})['monto_cuota']
    cosecha['Cartera Total (Capital Pagado)'] = df[df['estado'].isin(['Pagado a Tiempo','Pagado Retraso'])].set_index('fecha_venta').resample(frecuencia).agg({'monto_cuota':'sum'})['monto_cuota']
    cosecha['Cartera Otorgada (Capital Desembolsado)'] = df.drop_duplicates(subset=['id_credito']).set_index('fecha_venta').resample(frecuencia).agg({'precio_venta':'sum'})['precio_venta']
    cosecha['Promedio monto de capital'] = df.drop_duplicates(subset=['id_credito']).set_index('fecha_venta').resample(frecuencia).agg({'precio_venta':'mean'})['precio_venta']
    
    cosecha['Cartera Pendiente vs Cartera Otorgada'] = cosecha['Cartera Total (Capital Pendiente)']/cosecha['Cartera Otorgada (Capital Desembolsado)']*100
    cosecha['Cartera Pagada vs Cartera Otorgada'] = cosecha['Cartera Total (Capital Pagado)']/cosecha['Cartera Otorgada (Capital Desembolsado)']*100
    
    cosecha['Créditos activos'] = df[df['estado']=='Fijo'].set_index('fecha_venta').resample(frecuencia).agg({'id_credito':'nunique'})['id_credito']
    cosecha['Créditos otorgados'] = df.set_index('fecha_venta').resample(frecuencia).agg({'id_credito':'nunique'})['id_credito']
    
    cosecha.drop(columns=['fecha_cuota'], inplace=True)

    result  = cosecha.T

    columnas  = result.columns
    columnas_clean = []

    for columna in columnas:
        columna = str(columna)
        if columna == 'fecha_venta':
            name = 'Indicador'
        else:
            if frecuencia=='M':
                name = 'Mes '+columna.split('-')[1]
            else:
                name = 'Quincena '+columna.split('-')[2].split(' ')[0]+'/'+columna.split('-')[1]
        
        columnas_clean.append(name)

    result.columns = columnas_clean

    return result


# Mora monto
def mora_monto(df, c=False):

    if c==False:
        estados = ['Vencido']
    else:
        estados = ['Vencido', 'Exigible', 'Fijo']
        df = df[df['estado_mora'].isin(['Mora 15','Mora 30','Mora 45','Mora 60'])]

    df_vencido = df[df['estado'].isin(estados)]
    df_vencido_pivot =df_vencido.pivot_table(columns='fecha_venta',index='estado_mora',values='monto_cuota',aggfunc='sum')

    result = df_vencido_pivot.T.reset_index().set_index('fecha_venta').resample('M').sum().T

    result.columns.name = 'Cosecha'
    result.index.name = 'Mora'

    result.columns = result.columns.strftime("%b %Y")

    return result

# Mora saldo

# AUX

def mora_saldo_estado(df, estado, c=False):

    if c==False:
        estados=['Vencido']
    else:
        estados=['Vencido','Exigible','Fijo']
    
    df = df[df['estado_mora']==estado]
    df_vencido = df[df['estado'].isin(estados)]

    result = df_vencido.set_index('fecha_venta').resample('M')['monto_cuota'].sum()/df.drop_duplicates(subset=['id_credito']).set_index('fecha_venta').resample('M')['saldo_actual'].sum()
    
    return result


def mora_saldo(df, c=False):
    result = pd.DataFrame([mora_saldo_estado(df,'Mora 15',c),
                    mora_saldo_estado(df,'Mora 30',c),
                    mora_saldo_estado(df,'Mora 45',c),
                    mora_saldo_estado(df,'Mora 60',c)
                          ])
    
    result = result.T

    result.columns = ['Mora 15','Mora 30','Mora 45','Mora 60']

    result.index.name = 'Cosecha'
    result.index = result.index.strftime('%b %Y')

    return result.T

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
    df = clean(df, start_date, end_date, pais)
    return df

original_df = load_data('cashflow.csv')

if "df" not in st.session_state:
    st.session_state.df = clean_data(original_df)

if "pais" not in st.session_state:
    st.session_state.pais = ['El Salvador','Honduras']

df = st.session_state.df

tablas = [
        ('Análisis de Cosecha',analisis_cosecha(clean(df, pais=st.session_state.pais))),
        ('Mora - Monto',mora_monto(clean(df, pais=st.session_state.pais))),
        ('Mora vs Saldo Actual',mora_saldo(clean(df, pais=st.session_state.pais))),
        ('Mora Contagiada - Monto',mora_monto(clean(df, pais=st.session_state.pais), c=True)),
        ('Mora Contagiada vs Saldo Actual',mora_saldo(clean(df, pais=st.session_state.pais), c=True))
         ]

@st.cache_resource
def generate_report():
    file = pdf.create_pdf_report(tablas, "analisis_cosecha.pdf")
    return file

report = generate_report()

with open("analisis_cosecha.pdf", "rb") as file:
    btn = st.download_button(
        label="Descargar PDF",
        data=file,
        file_name="analisis_cosecha.pdf",
        mime="application/pdf"
    )

# Analisis cosecha
st.header(tablas[0][0])
st.dataframe(tablas[0][1])

# Mora - Monto
st.header(tablas[1][0])
st.dataframe(tablas[1][1], column_config=column_config_dinero)

# Mora vs saldo actual
st.header(tablas[2][0])
st.dataframe(tablas[2][1])#, column_config=column_config_cantidad)

# Mora contagiada monto
st.header(tablas[3][0])
st.dataframe(tablas[3][1], column_config=column_config_dinero)

# Mora contagiada vs saldo
st.header(tablas[4][0])
st.dataframe(tablas[4][1], column_config=column_config_cantidad)
