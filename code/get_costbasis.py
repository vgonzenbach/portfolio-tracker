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
    sell_df = df[(df.Transaction == 'SELL') & (df.Date >= f'{year}-01-01') & (df.Date <= f'{year}-12-31')]

    pairs = []
    for asset in pd.unique(sell_df.Asset):
        
        for s, sale in sell_df[sell_df.Asset == asset].iterrows():
            buy_df = df[(df.Transaction == 'BUY') & (df.Asset == asset)].loc[:s].sort_values(by='Asset Price', ascending=False) 
            
            for b, buy in buy_df.iterrows():
                
                diff = buy['Asset Amount'] - sale['Asset Amount']
                if (diff > 0): # Is the highest buy enough to cover this sale?
                    
                    buy['Asset Amount'] = sale['Asset Amount']
                    pairs.append(list(sale) + list(buy))

                    df.loc[b, 'Asset Amount'] = diff # Discount sell from buy amt in transaction record
                    break # Go to next sale

                elif (diff <= 0):
                    
                    sale['Asset Amount'] = buy['Asset Amount']
                    pairs.append(list(sale) + list(buy))
                    
                    df = df.drop(b)
                    buy_df = buy_df.drop(b)
                    sale['Asset Amount'] = abs(diff)

    pairs_df = pd.DataFrame.from_records(pairs)
    pairs_df.columns = [col + ' (Sell)' for col in list(df.columns)] + [col + ' (Buy)' for col in list(df.columns)]

    pairs_df['Cost Basis (Sell)'] = pairs_df['Asset Price (Sell)'] * pairs_df['Asset Amount (Sell)']
    pairs_df['Cost Basis (Buy)'] = pairs_df['Asset Price (Buy)'] * pairs_df['Asset Amount (Buy)']
    return pairs_df
