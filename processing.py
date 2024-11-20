"""Funciones de transformación y limpieza de datos"""

import numpy as np 
import pandas as pd 
import datetime 
from datetime import date, timedelta 

today = date.today()

def clean_cashflow_data(df):
    # Step 1: Handle missing values
    # For now, we will fill missing numerical columns with 0 and missing categorical columns with 'Unknown'
    numerical_columns = ['saldo_total', 'monto_cuota', 'saldo_exigible', 'monto_seguro', 'cuota_moneda', 'exigible_moneda']
    categorical_columns = ['estado', 'fecha_pago', 'estatus']
    
    # Fill missing numerical values with 0 (you can customize this to use mean or median if appropriate)
    df[numerical_columns] = df[numerical_columns].fillna(0)
    
    # Fill missing categorical values with 'Unknown' or appropriate values
    df[categorical_columns] = df[categorical_columns].fillna('Unknown')
    
    # Step 2: Ensure data types are correct
    # Convert date fields to datetime format
    df['fecha_cuota'] = pd.to_datetime(df['fecha_cuota'], errors='coerce')
    df['fecha_pago'] = pd.to_datetime(df['fecha_pago'], errors='coerce')
    
    df['semana_cuota'] = df['fecha_cuota'].dt.isocalendar().week
    df['mes_cuota'] = df['fecha_cuota'].dt.month

    # Step 3: Remove duplicate rows if any
    df = df.drop_duplicates()
    
    df['estado'] = df['estado'].map({'Pagado a Tiempo':'Pagado',
                                                  'Pagado Retraso':'Pagado',
                                                  'Vencido':'Impago',
                                                  'Exigible':'Fijo',
                                                  'Fijo':'Fijo'})
    # Step 4: Standardize categorical fields (e.g., ensuring consistent formatting in 'estado')
    df['estado'] = df['estado'].str.strip().str.title()  # Example standardization
    
    return df

def add_loan_analysis_columns_with_cohort(df):
    # Step 1: Calculate Loan Age (in days)
    df['loan_age_days'] = 14 + (df['num_cuota'] - 1) * 15
    
    # Step 2: Calculate Loan Start Date
    df['loan_start_date'] = df['fecha_cuota'] - pd.to_timedelta(df['loan_age_days'], unit='D')
    
    # Step 3: Define Cohort (Vintage) based on biweekly loan start periods
    df['vintage_biweekly'] = df['loan_start_date'].dt.to_period('2W-SUN')
    
    # Step 4: Create abbreviated cohort labels based on the start month and biweekly period
    df['year'] = df['vintage_biweekly'].apply(lambda x: str(x.start_time.year)[-2:])  # Last 2 digits of the year
    df['month'] = df['vintage_biweekly'].apply(lambda x: str(x.start_time.month).zfill(2))  # Month from start time
    df['cohort_num'] = df['vintage_biweekly'].apply(lambda x: 'Q1' if x.start_time.day <= 15 else 'Q2')
    
    # Create the abbreviated cohort label (e.g., '24M07q1' for the first cohort in July 2024)
    df['abbreviated_cohort'] = df['year'] + 'M' + df['month'] + df['cohort_num']
 
    return df


def assign_default_paid_status(df):
    # Sort the dataframe by installment number to ensure sequential processing
    df = df.sort_values(by=['id_credito','num_cuota'])
    
    # Initialize a counter for consecutive missed payments
    consecutive_missed_payments = 0
    
    # Iterate through each installment for the loan
    for idx, row in df.iterrows():
        # If the payment was made (any type of "Pagado" status), reset the missed payments counter
        if 'Pagado' in row['estado']:
            df.at[idx, 'default_status'] = 'Pagado'
            consecutive_missed_payments = 0  # Reset the missed payment count

            df.at[idx, 'consecutive_missed_payments'] = consecutive_missed_payments

        elif 'Fijo' in row['estado']:
            df.at[idx, 'default_status'] = 'Fijo'
            consecutive_missed_payments = 0

            df.at[idx, 'consecutive_missed_payments'] = consecutive_missed_payments

        else:
            # Increment the missed payments counter
            consecutive_missed_payments += 1
            # Assign the default status based on the number of consecutive missed payments
            df.at[idx, 'default_status'] = f'Mora {consecutive_missed_payments}'
            df.at[idx, 'consecutive_missed_payments'] = consecutive_missed_payments
    
    return df

def join_clients_with_loans(loans_df, clients_df):
    """
    This function joins the CLIENTS table with the current loans table on the 'id_credito' key.
    
    Parameters:
    - loans_df: DataFrame containing the loans data (the current table)
    - clients_df: DataFrame containing the CLIENTS data with additional loan information
    
    Returns:
    - A DataFrame resulting from joining both tables on 'id_credito'.
    """
    # Perform a left join on 'id_credito' (assuming we want to keep all loans)
    joined_df = loans_df.merge(clients_df, how='left', on='id_credito')
    
    return joined_df


##########################################

def prep_pipeline(df, info_df): # CAMBIAR A CONEXIÓN
    #df = pd.read_csv(cashflow_file_path)
    #info_df = pd.read_csv(clients_file_path)

    df = clean_cashflow_data(df)
    df = add_loan_analysis_columns_with_cohort(df)
    df = assign_default_paid_status(df)

    info_df = info_df[info_df['id_credito'].isin(df['id_credito'].unique())]
    info_df = info_df[['id_credito','nombre_cliente','vendedor','nombre_empresa','nombre_sucursal','nombre_fabricante','pais']]

    clean_df = join_clients_with_loans(df,info_df)

    clean_df['pago'] = clean_df['estado'].map({'Pagado A Tiempo':1,
                                           'Pagado Retraso':1,
                                           'Pagado':1,
                                           'Vencido':0,
                                           'Impago':0,
                                           'Exigible':np.nan,
                                           'Fijo':np.nan})
    clean_df['impago'] = [1 if x==0 else 0 for x in clean_df['pago']]
    
    clean_df['monto_recibido'] = clean_df['monto_cuota'] * clean_df['pago']
    clean_df['monto_esperado'] = clean_df['num_cuota']*clean_df['monto_cuota']

    clean_df.sort_values(by=['id_credito','num_cuota'], inplace=True)

    s = clean_df.groupby(['id_credito','num_cuota'])['monto_recibido'].sum()
    s = s.groupby(level='id_credito').cumsum()

    v = clean_df.groupby(['id_credito','num_cuota'])['impago'].sum()
    v = v.groupby(level='id_credito').cumsum()

    l = clean_df.groupby(['id_credito','num_cuota'])['pago'].sum()
    l = l.groupby(level='id_credito').cumsum()

    clean_df['recibido_acumulado'] = s.values
    clean_df['impago_acumulado'] = v.values
    clean_df['pago_acumulado'] = l.values

    #clean_df['default_status'] = ['Mora '+str(value) if value!=0 else 'Fijo' for value in clean_df['impago_acumulado']]
    #clean_df['default_status'] = clean_df['default_status'].where(clean_df['pago']!=1,'Pagado')

    return clean_df, info_df

#########################################

def filter_loans(loans_df, categorical_filters=None, date_column=None, start_date=None, end_date=None):
    """
    This function filters the loans DataFrame based on categorical columns and/or a date range.
    
    Parameters:
    - loans_df: The DataFrame containing loan records.
    - categorical_filters: A dictionary where keys are column names and values are lists of accepted values (e.g., {'default_status': ['Paid', 'Default 2']}).
    - date_column: The name of the column containing dates to apply a date filter.
    - start_date: The start date for filtering (optional).
    - end_date: The end date for filtering (optional).
    
    Returns:
    - A filtered DataFrame based on the provided criteria.
    """
    filtered_df = loans_df.copy()
    
    # Step 1: Apply categorical filters (if provided)
    if categorical_filters:
        for column, accepted_values in categorical_filters.items():
            filtered_df = filtered_df[filtered_df[column].isin(accepted_values)]
    
    # Step 2: Apply date range filter (if date_column is provided)
    if date_column and (start_date or end_date):
        if start_date:
            filtered_df = filtered_df[filtered_df[date_column] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df[date_column] <= pd.to_datetime(end_date)]
    
    return filtered_df


##########################################


def latest(clean_df, info_df):
    today = pd.Timestamp.now()
    
    # Step 1: Filter the dataset to include records up to today's date
    current_data = clean_df[clean_df['fecha_cuota'] <= today]
    
    # Step 2: Find the most recent record for each loan (id_credito)
    latest_records = current_data.sort_values('fecha_cuota').groupby('id_credito').tail(1)
    
    # Step 3: Define a function to calculate the paid amount based on the default status
    def calculate_paid_amount(row):
        # For Paid status, the total paid amount is num_cuota * monto_cuota
        if row['default_status'] == 'Paid':
            return row['num_cuota'] * row['monto_cuota']
        
        # For Default status, calculate the number of installments that were actually paid
        elif 'Default' in row['default_status']:
            # Extract the number of consecutively missed installments from the 'default_status'
            missed_cuotas = int(row['default_status'].split(' ')[1])  # Extract the number from 'Default X'
            paid_installments = max(0, row['num_cuota'] - missed_cuotas)  # Ensure no negative installments
            return paid_installments * row['monto_cuota']
        
        return 0  # For other cases (if any)
    
    # Apply the paid amount calculation
    latest_records['paid_amount'] = latest_records.apply(calculate_paid_amount, axis=1)
    
    # Step 4: Add a column for 'expected_amount' based on num_cuota * monto_cuota
    latest_records['expected_amount'] = latest_records['num_cuota'] * latest_records['monto_cuota']
    latest_records['monto_vencido_acumulado'] = latest_records['monto_esperado'] - latest_records['recibido_acumulado']

    #data = join_clients_with_loans(latest_records, info_df)
    
    # Return the final table with relevant columns
    return latest_records

##########################################

def top_10_category_values(df, categorical_column, rank_by='count', metric_column=None):
    """
    This function returns a table of the top 10 category values based on the specified ranking criteria.
    
    Parameters:
    - df: The DataFrame containing the joined loans and clients data.
    - categorical_column: The categorical column to analyze (e.g., 'client_type', 'default_status').
    - rank_by: The metric to rank by (options: 'count', 'default_rate', 'money_recovered').
    - metric_column: Column to use for calculations (required for 'money_recovered' and 'default_rate').
    
    Returns:
    - A DataFrame of the top 10 category values based on the chosen ranking criteria.
    """
    result = None
    
    # Step 1: Group the data by the specified categorical column
    grouped = df.groupby(categorical_column)
    
    # Step 2: Calculate based on the chosen ranking criteria
    if rank_by == 'count':
        # Count of unique clients/loans
        result = grouped['id_credito'].nunique().nlargest(10).reset_index(name='count')
    
    elif rank_by == 'default_rate':
        # Default rate: total defaults / total loans
        if not metric_column:
            raise ValueError("metric_column is required for 'default_rate'")
        total_loans = grouped['id_credito'].nunique()
        total_defaults = grouped.apply(lambda x: x[x['default_status'].str.contains('Default')]['id_credito'].nunique())
        result = (total_defaults / total_loans).nlargest(10).reset_index(name='default_rate')
    
    elif rank_by == 'money_recovered':
        # Money recovered: sum of 'paid_amount' column
        if not metric_column:
            raise ValueError("metric_column is required for 'money_recovered'")
        result = grouped[metric_column].sum().nlargest(10).reset_index(name='money_recovered')
    
    return result

###################################
#cashflow_file_path = 'cashflow.csv'
#clients_file_path = 'clients.csv'

#clean_df, info_df = prep_pipeline(cashflow_file_path, clients_file_path)
#latest = latest(clean_df,info_df)