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
    elif type == 'calender':
        df['A-Detector'] = df['A-Detector'].map({
            1 : True,
            0 : False,
            'TRUE': True,
            'FALSE' : False,
            '1' : True,
            '0' : False
        })
        # df['is_Anchor'] = df['is_Anchor'].map({
        #     1 : True,
        #     0 : False,
        #     'TRUE': True,
        #     'FALSE' : False,
        #     '1' : True,
        #     '0' : False
        # })
    else:
        df['Release Date'] = df['Release Date'].astype(str)
        df['A-Detector'] = df['A-Detector'].map({
            1 : True,
            0 : False,
            'TRUE': True,
            'FALSE' : False,
            '1' : True,
            '0' : False
        })
        
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
        copy_df = df.copy()
        copy_df['Release Date'] = pd.to_datetime(copy_df['Release Date'], errors='coerce', dayfirst=True)
        copy_df['A-Detector'] = copy_df['A-Detector'].map({
            1 : True,
            0 : False,
            'TRUE': True,
            'FALSE' : False,
            '1' : True,
            '0' : False
        })
        today = pd.to_datetime(date.today())

        for idx in copy_df.index:
            if pd.notna(copy_df.at[idx, 'Release Date']):
                if copy_df.at[idx, 'Release Date'] < today:
                    df.at[idx, 'Release Status'] = 1
                else:
                    df.at[idx, 'Release Status'] = 0

        return df
