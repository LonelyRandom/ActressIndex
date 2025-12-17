import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import date,datetime
import streamlit as st

def values_handling(df, type):
    if type == 'actress':
        df['Height (cm)'] = df['Height (cm)'].astype(str)
        df['Age'] = df['Age'].astype(str)
        df['Birthdate'] = df['Birthdate'].astype(str)
        df['Debut Date'] = df['Debut Date'].astype(str)
        df['Retire Date'] = df['Retire Date'].astype(str)
    else:
        df['Release Date'] = df['Release Date'].astype(str)
        
    return df

def initial_load(df):
    for idx in df.index:
        if df.at[idx,'Birthdate'] != '?':
            if isinstance(df.at[idx,'Birthdate'], str):
                birthdate = datetime.strptime(df.at[idx,'Birthdate'], '%d/%m/%Y').date()
                age = relativedelta(date.today(), birthdate).years
        
        if df.at[idx,'Debut Date'] != '?' and df.at[idx,'Retire Date'] == '?':
            if isinstance(df.at[idx,'Debut Date'], str):
                debut_date = datetime.strptime(df.at[idx,'Debut Date'], '%d/%m/%Y').date()
                period = relativedelta(date.today(), debut_date)

        elif df.at[idx,'Debut Date'] != '?' and df.at[idx,'Retire Date'] != '?':
            if isinstance(df.at[idx,'Debut Date'], str):
                debut_date = datetime.strptime(df.at[idx,'Debut Date'], '%d/%m/%Y').date()
            if isinstance(df.at[idx,'Retire Date'], str):
                retire_date = datetime.strptime(df.at[idx,'Retire Date'], '%d/%m/%Y').date()

            period = relativedelta(retire_date, debut_date)

        if period.months == 0:
            debut_period = f'{period.years} Year'
        else:
            debut_period = f'{period.years}  Year {period.months} Months'
        
        df.at[idx,'Age'] = age
        df.at[idx,'Debut Period'] =debut_period
    return df