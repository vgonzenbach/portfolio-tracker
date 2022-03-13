from itertools import dropwhile
from markupsafe import re
import read_data
import pandas as pd
import numpy as np
#import numpy as np
#from plotnine import *

# Use method
def get_costbasis(df):
    """Calculate average cost basis for an asset"""
    cb_df = pd.DataFrame(columns=['Asset', 'Buy Avg. CB', 'Sell Avg. CB', 'ROI'])
    
    records = []
    for asset in pd.unique(df.Asset):
        rec = {key: None for key in list(cb_df.columns)}
        asset_df = df[df.Asset == asset]
        rec['Asset'] = asset
        b_filter = asset_df.Transaction == 'BUY'
        rec['Buy Avg. CB'] = asset_df[b_filter]['Asset Price'].sum() / sum(b_filter)
        s_filter = asset_df.Transaction == 'SELL'
        rec['Sell Avg. CB'] = asset_df[s_filter]['Asset Price'].sum() / sum(s_filter)
        rec['ROI'] = 100*(rec['Sell Avg. CB'] / rec['Buy Avg. CB'])
        records.append(rec)
    
    cb_df = pd.DataFrame.from_records(records)
    return(cb_df)

def get_current_asset_amount(df):
    quantifier = [1 if t == 'BUY' else -1 for t in df['Transaction']] 
    df['qAmount'] = df['Asset Amount'] * quantifier

    amt_df = pd.DataFrame(columns=['Asset', 'Current Amount'])
    records = []
    for asset in pd.unique(df.Asset):
        rec = {key: None for key in list(amt_df.columns)}
        asset_df = df[df.Asset == asset]
        rec['Asset'] = asset
        rec['Amount'] = sum(asset_df['qAmount'])
        records.append(rec)
    return pd.DataFrame.from_records(records)

def pair_sales(df, rule='hifo', year=2021):
    df = df[df.Exchange != 'Fidelity']
    sale_in_year = [0 <= (date - pd.Timestamp(f'{year}-01-01 00:00:00+0000')).days <= 365 for date in df['Date']]
    sell_df = df[(df.Transaction == 'SELL') & sale_in_year]

    pairs = []
    for asset in pd.unique(sell_df.Asset):
        
        for s, sale in sell_df[sell_df.Asset == asset].sort_values(by='Asset Price', ascending=True).iterrows():

            buy_df = df[(df.Transaction == 'BUY') & (df.Asset == asset)].loc[:s].sort_values(by='Asset Price', ascending=False) 
            
            for b, buy in buy_df.iterrows():
                
                diff = buy['Asset Amount'] - sale['Asset Amount'] # Is the highest buy enough to cover this sale?
                if (diff > 0): # Yes
                    
                    #buy['Asset Amount'] = sale['Asset Amount']
                    amt = sale['Asset Amount']
                    buy['Cost Basis'] = buy['Asset Price'] * amt
                    sale['Cost Basis'] = sale['Asset Price'] * amt
                    buy['Fee'] = buy['Fee'] * (amt/buy['Asset Amount'])
                    buy['Asset Amount'] = amt
                    pairs.append(list(sale) + list(buy))

                    df.loc[b, 'Asset Amount'] = diff # Discount sell from buy amt in transaction record
                    df.loc[b, 'Fee'] = df.loc[b, 'Fee'] - buy['Fee']
                    break # Go to next sale

                elif (diff <= 0): # No
                    
                    amt = buy['Asset Amount']
                    buy['Cost Basis'] = buy['Asset Price'] * amt
                    sale['Cost Basis'] = sale['Asset Price'] * amt
                    
                    fee = sale['Fee']
                    sale['Fee'] = fee * (amt/sale['Asset Amount'])
                    sale['Asset Amount'] = amt
                    pairs.append(list(sale) + list(buy))

                    df = df.drop(b)
                    buy_df = buy_df.drop(b)
                    sale['Asset Amount'] = abs(diff)
                    sale['Fee'] = fee - sale['Fee']

    pairs_df = pd.DataFrame.from_records(pairs)
    pairs_df.columns = [col + ' (Sell)' for col in list(df.columns)] + [col + ' (Buy)' for col in list(df.columns)]

    pairs_df['Date (Sell)'] = [ts.strftime('%m-%d-%Y') for ts in pairs_df['Date (Sell)']]
    pairs_df['Date (Buy)'] = [ts.strftime('%m-%d-%Y') for ts in pairs_df['Date (Buy)']]

    return pairs_df
