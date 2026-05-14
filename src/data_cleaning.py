# Cleaning the data collected from Louisville Metro Open Data Portal (https://data.louisvilleky.gov/)

import pandas as pd

def delete_not_dronable(dataframe):
    # Delete incidents that are not dronable
    dronable_nibrs_codes = [
        '720',
        '200',
        '13A',
        '13B',
        '220',
        '620',
        '290',
        '35A',
        '49A',
        '49B',
        '49C',
        '09A',  
        '09B',
        '09C',
        '64A',
        '64B',
        '30C',
        '100',
        '23B',
        '23C',
        '23F',
        '23G',
        '240',
        '40A',
        '40B',
        '120',
        '280',
        '520',
        '521',
        '522',
        '526',
        '90B',
        '90C',
        '90D',
        '90J',
    ]
    dataframe = dataframe[dataframe['nibrs_code'].isin(dronable_nibrs_codes)]
    return dataframe



dataframe = pd.read_excel('./data/cleaned_LMPD_data_2025.xlsx')
dataframe = delete_not_dronable(dataframe)
