"""Funciones Reportes"""

import numpy as np 
import pandas as pd 
import datetime 
from datetime import date, timedelta 

def clean(df, start_date=False, end_date=False, pais=None):

    df = df[~df['nombre_empresa'].isin(['(ANTERIOR) INVERSIONES EBEN EZER', 'GALO CELL', 'INVERSIONES EBEN EZER'])]

    # Limpiar columnas de tiempo
    df['fecha_cuota'] = pd.to_datetime(df['fecha_cuota'])
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])

    # Agregar estado de mora
    
    estado_mora = {'Al día':[None, 0, np.nan],
                   'Mora 15':range(1,30),
                'Mora 30':range(30,45),
                'Mora 45':range(45,60),
                'Mora 60':range(60,120)}


    df['estado_mora'] = None

    for index in df['dias_atraso'].index:
        for key in estado_mora:
            value = df['dias_atraso'][index]
            if value in estado_mora[key]:
                df.at[index,'estado_mora'] = key

    #df['estado_mora'] = df['estado_mora'].astype(str).replace('None','al dia')

    # Agregar grupo pendiente o pagado
    #df['grupo'] = ['Pagado' if value not in ['Fijo','Exigible','Vencido'] else 'Pendiente' for value in df['estado']]

    # Filtros
    if pais!=None:
        clean_df = df[df['pais'].isin(pais)]
    
    if start_date==False:
        start_date = min(df['fecha_cuota'])
    else:
        start_date = np.datetime64(start_date)
    
    if end_date==False:
        end_date = max(df['fecha_cuota'])
    else:
        end_date = np.datetime64(end_date)
    
    clean_df = df[(df['fecha_cuota']>=start_date)&(df['fecha_cuota']<=end_date)]
    
    if pais!=None:
        clean_df = df[df['pais'].isin(pais)]


    return clean_df


# TABLA INDICADORES CARTERA PENDIENTE
def indicadores_cartera_pendiente(data, formato=False):

    # Cartera otorgada
    cartera_otorgada = sum(data['monto_cuota'])

    # Sumatoria de todas las cuotas pagadas
    cartera_pagado = sum(data[data['estado'].isin(['Pagado a Tiempo','Pagado Retraso'])]['monto_cuota'])

    # Pendiente por estado de mora (fijo, exigible o vencido)
    df = data[data['estado'].isin(['Fijo','Exigible','Vencido'])]

    # Monto por cobrar por estado de mora
    pendiente_estado = dict(df.groupby('estado_mora')['monto_cuota'].sum())
    try: cartera_al_dia = pendiente_estado['Al día'] 
    except: cartera_al_dia = 0
    try: cartera_vencido = pendiente_estado['Mora 15']
    except: cartera_vencido = 0
    try: cartera_legal = pendiente_estado['Mora 30']
    except:cartera_legal = 0
    try: cartera_castigado = pendiente_estado['Mora 45']
    except:cartera_castigado=0
    try: cartera_castigado2 = pendiente_estado['Mora 60']
    except:cartera_castigado2=0

    # Monto cartera total
    cartera_total = sum(df['monto_cuota'])

    tabla = {'Cartera Al día': cartera_al_dia,
             'Cartera Mora 15': cartera_vencido,
             'Cartera Mora 30': cartera_legal,
             'Cartera Mora 45': cartera_castigado,
             'Cartera Mora 60':cartera_castigado2,
             'Cartera total': cartera_total,
             'Cartera pagado': cartera_pagado,
             'Cartera otorgada': cartera_otorgada}
    # Hay que reset index
    
    indicadores = pd.DataFrame.from_dict(tabla, orient='index').rename(columns={0:'Monto (USD)'}).reset_index()
    indicadores['Porcentaje'] = indicadores['Monto (USD)']/cartera_otorgada*100

    indicadores_formato = indicadores.copy()
    indicadores_formato['Monto (USD)'] = [f"$ {round(value,2)}" for value in indicadores_formato['Monto (USD)']]
    indicadores_formato['Porcentaje'] = [f"{round(value,2)}%" for value in indicadores_formato['Porcentaje']]


    if formato==False:
        return indicadores
    
    else:
        return indicadores_formato



# TABLA CREDITOS OTORGADOS
def indicadores_creditos_otorgados(df, formato=False):

    df = df.sort_values(by=['id_credito','dias_atraso']).drop_duplicates(subset=['id_credito'], keep='last')

    creditos_otorgados = pd.DataFrame({'index':['Créditos Al Día', 'Créditos Mora 15','Créditos Mora 30', 'Créditos Mora 45', 'Créditos Mora 60',
                                               'Créditos activos', 'Créditos saldados', 'Créditos a pérdida',
                                               'Créditos otorgados'],
                                    'Cantidad':[len(df[df['estado_mora']=='Al día']['id_credito'].unique()), # al dia
                                                len(df[df['estado_mora']=='Mora 15']['id_credito'].unique()), # vencidos
                                                len(df[df['estado_mora']=='Mora 30']['id_credito'].unique()), # legal
                                                len(df[df['estado_mora']=='Mora 45']['id_credito'].unique()), # castigado
                                                len(df[df['estado_mora']=='Mora 60']['id_credito'].unique()), # castigado2
                                                len(df[df['estado'].isin(['Fijo'])]['id_credito'].unique()), # activo
                                                len(df.loc[df['estado'] != 'Fijo', 'id_credito'].unique()), # saldado 
                                                len(df[df['estado_mora']=='Mora 60']['id_credito'].unique()), # perdida
                                                len(df['id_credito'].unique()) # otorgados
                                                ]}) # No hay que reset index
    
    creditos_otorgados['Porcentaje'] = creditos_otorgados['Cantidad']/len(df['id_credito'].unique())*100
    creditos_otorgados_formato = creditos_otorgados.copy()
    creditos_otorgados_formato['Porcentaje'] = [f"{round(value,2)}%" for value in creditos_otorgados_formato['Porcentaje']]

    if formato==False:
        return creditos_otorgados
    else:
        return creditos_otorgados_formato


# TABLA MONTOS
def indicadores_montos(df):
    # No hay que reset index
    montos = pd.DataFrame({'Monto':['Capital promedio otorgado', 'Plazo promedio en cuotas'],
                       'Valores':['$'+str(round(df.drop_duplicates(subset=['id_credito'])['precio_venta'].mean(),2)), round(df.drop_duplicates(subset=['id_credito'])['numero_periodos'].mean())]})
    #montos.iloc[0] = f'$ {round(montos.iloc[0],2)}'
    #montos.iloc[1] = round(montos.iloc[1])

    return montos


# TABLAS MORA Y MORA C VS SALDO ACTUAL
def indicadores_mora_saldo(df, c=False):

    cartera_pendiente = sum(df[~df['estado'].isin(['Pagado a Tiempo','Pagado Retraso'])]['monto_cuota'])

    if c==True:
        estados_cuotas = ['Vencido','Fijo','Exigible']
    else:
        estados_cuotas = ['Vencido']

    # Mora saldo
    data = df[(df['estado'].isin(estados_cuotas))&(df['estado_mora']!='al dia')]

    grouped = data.groupby('estado_mora')['monto_cuota'].sum()
    mora_estado = dict(grouped)

    lista_estados = ['Mora 15','Mora 30','Mora 45','Mora 60']
    for item in lista_estados:
        if item not in list(grouped.index):
            mora_estado[item] = 0

    mora_estado['Total'] = sum(data['monto_cuota'])

    mora_saldo = pd.DataFrame.from_dict(mora_estado, orient='index').rename(columns={0:'Monto (USD)'}).reset_index() #hay que reset index
    mora_saldo['Porcentaje'] = mora_saldo['Monto (USD)']/cartera_pendiente*100

    return mora_saldo


# TABLA CREDITOS EN MORA VS ACTIVOS
def indicadores_mora_creditos(df):
    data = df[(df['estado_mora']!='al dia')&(df['estado']=='Vencido')]

    grouped = data.groupby('estado_mora')['id_credito'].nunique()
    creditos_estados = dict(grouped)

    lista_estados = ['Mora 15','Mora 30','Mora 45', 'Mora 60']
    for item in lista_estados:
        if item not in list(grouped.index):
            creditos_estados[item] = 0

    creditos_estados['Total'] = len(data['id_credito'].unique())

    mora_creditos = pd.DataFrame.from_dict(creditos_estados, orient='index').rename(columns={0:'Cantidad'}).reset_index() # Hay que reset index
    mora_creditos['Porcentaje'] = mora_creditos['Cantidad']/len(df.loc[df['estado'] == 'Fijo', 'id_credito'].unique())*100

    return mora_creditos


##############################
# Clean especial
def clean_reportes(df):
    df['fecha_cuota'] = pd.to_datetime(df['fecha_cuota'])
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])

    today = datetime.date.today()
    df['dias_atraso_cuota'] = [today-fecha for fecha in df['fecha_cuota'].dt.date]
    df['dias_atraso_cuota'] = df['dias_atraso_cuota'].dt.days
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
    cosecha['Cartera Total (Capital Pendiente)'] = df.drop_duplicates(subset=['id_credito']).set_index('fecha_venta').resample(frecuencia).agg({'saldo_actual':'sum'})['saldo_actual']
    #cosecha['Cartera Total (Capital Pendiente)'] = df[df['estado']=='Fijo'].set_index('fecha_venta').resample('M').agg({'monto_cuota':'sum'})['monto_cuota']
    cosecha['Cartera Total (Capital Pagado)'] = df[df['estado'].isin(['Pagado a Tiempo','Pagado Retraso'])].set_index('fecha_venta').resample(frecuencia).agg({'monto_cuota':'sum'})['monto_cuota']
    cosecha['Cartera Otorgada (Capital Desembolsado)'] = df.drop_duplicates(subset=['id_credito']).set_index('fecha_venta').resample(frecuencia).agg({'valor_financiamiento':'sum'})['valor_financiamiento']
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
        df = df[df['estado_mora']!='Al día']

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
                    mora_saldo_estado(df,'Mora 60',c)],)
    
    result = result.T

    result.columns = ['Mora 15','Mora 30','Mora 45','Mora 60']

    result.index.name = 'Cosecha'
    result.index = result.index.strftime('%b %Y')

    return result.T


