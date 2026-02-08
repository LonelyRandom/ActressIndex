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

def initial_load(df, type):
    if type == 'actress':
        for idx in df.index:
            if df.at[idx,'Birthdate'] != '?':
                if isinstance(df.at[idx,'Birthdate'], str):
                    birthdate = datetime.strptime(df.at[idx,'Birthdate'], '%d/%m/%Y').date()
                    age = relativedelta(date.today(), birthdate).years
                    df.at[idx,'Age'] = age
            else:
                df.at[idx,'Age'] = '?'
                
            
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

            if df.at[idx, 'Debut Date'] != '?':
                if period.months == 0:
                    debut_period = f'{period.years} Year'
                else:
                    debut_period = f'{period.years}  Year {period.months} Months'

                df.at[idx,'Debut Period'] =debut_period
            else:
                df.at[idx,'Debut Period'] = '?'
        return df
    else:
    #     for idx in df.index:
    #         if df.at[idx, 'Release Date'] != '?':
    #             if isinstance(df.at[idx,'Release Date'], str):
    #                 release_date = datetime.strptime(df.at[idx,'Release Date'], '%d/%m/%Y').date()
    #                 today = date.today()

    #                 # Bandingkan dengan tanggal hari ini
    #                 if release_date < today:
    #                     df.at[idx, 'Release Status'] = 1.0  # Sudah rilis
    #                 else:
    #                     df.at[idx, 'Release Status'] = 0.0  # Belum rilis
        
        return df
