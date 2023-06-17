from itertools import dropwhile
from markupsafe import re
import read_data
import pandas as pd
import numpy as np
#import numpy as np
#from plotnine import *

# Use method
def get_costbasis(df):
    """Calculate average cost_basis for an asset"""
    cb_df = pd.DataFrame(columns=['asset', 'Buy Avg. CB', 'Sell Avg. CB', 'ROI'])
    
    records = []
    for asset in pd.unique(df.asset):
        rec = {key: None for key in list(cb_df.columns)}
        asset_df = df[df.asset == asset]
        rec['asset'] = asset
        b_filter = asset_df.type == 'BUY'
        rec['Buy Avg. CB'] = asset_df[b_filter]['price'].sum() / sum(b_filter)
        s_filter = asset_df.type == 'SELL'
        rec['Sell Avg. CB'] = asset_df[s_filter]['price'].sum() / sum(s_filter)
        rec['ROI'] = 100*(rec['Sell Avg. CB'] / rec['Buy Avg. CB'])
        records.append(rec)
    
    cb_df = pd.DataFrame.from_records(records)
    return(cb_df)

def get_current_asset_amount(df):
    quantifier = [1 if t == 'BUY' else -1 for t in df['type']] 
    df['qAmount'] = df['amount'] * quantifier

    amt_df = pd.DataFrame(columns=['asset', 'Current Amount'])
    records = []
    for asset in pd.unique(df.asset):
        rec = {key: None for key in list(amt_df.columns)}
        asset_df = df[df.asset == asset]
        rec['asset'] = asset
        rec['Amount'] = sum(asset_df['qAmount'])
        records.append(rec)
    return pd.DataFrame.from_records(records)

def pair_sales(df, rule='hifo', year=2021):
    """
    Returns a DataFrame containing pairs of buy and sell types in order to optimize tax losses for a given year.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing type history with columns including 'type', 'asset', 'date', 'amount', 
        'price', 'fee', and 'exchange'.
    rule : str, optional
        A string indicating the rule to be used for determining which shares are sold when multiple purchases have been made. 
        Default is 'hifo' which stands for highest-in, first-out.
    year : int, optional
        An integer indicating the year for which tax loss optimization is being done. Default is 2021.

    Returns:
    --------
    pandas.DataFrame
        A DataFrame containing pairs of buy and sell types that optimize tax losses for a given year. The columns 
        in the DataFrame include 'type (Sell)', 'asset (Sell)', 'date (Sell)', 'amount (Sell)', 'price (Sell)', 
        'fee (Sell)', 'exchange (Sell)', 'cost_basis (Sell)', 'type (Buy)', 'asset (Buy)', 'date (Buy)', 'amount (Buy)', 
        'price (Buy)', 'fee (Buy)', 'exchange (Buy)', 'cost_basis (Buy)'.
    """
    df = df[df.exchange != 'Fidelity']
    sale_in_year = [0 <= (date - pd.Timestamp(f'{year}-01-01 00:00:00')).days <= 365 for date in df['date']] # Filter types within the given year
    sell_df = df[(df.type == 'SELL') & sale_in_year]  # Select all sell types within the given year

    pairs = []
    for asset in pd.unique(sell_df.asset):# For each unique asset that was sold in the year

        for s, sale in sell_df[sell_df.asset == asset].sort_values(by='price', ascending=True).iterrows():  # Sort the sell types by price and loop over each sell type
            # Select the buy types that occurred before the sell type and sort them by price in descending order
            buy_df = df[(df.type == 'BUY') & (df.asset == asset)].loc[:s].sort_values(by='price', ascending=False) 
            
            for b, buy in buy_df.iterrows(): # Loop over each buy type
                
                diff = buy['amount'] - sale['amount'] # Determine if the amount of the buy type is greater than, equal to, or less than the amount of the sell type
                if (diff > 0): # If the buy amount is greater than the sell amount: need to adjust the existing buy after pairing
                    amt = sale['amount']
                    buy['cost_basis'] = buy['price'] * amt # Calculate the cost_basis of the buy type
                    sale['cost_basis'] = sale['price'] * amt # Calculate the cost_basis of the sell type
                    buy['fee'] = buy['fee'] * (amt/buy['amount']) # Adjust the fee of the buy type proportionally to the amount sold
                    buy['amount'] = amt # Update the amount of the buy type to match the amount sold in the sell type
                    pairs.append(list(sale) + list(buy)) # Add the sell and buy types to the list of pairs

                    df.loc[b, 'amount'] = diff # Update the amount of the buy type to reflect the remaining amount after the sell type
                    df.loc[b, 'fee'] = df.loc[b, 'fee'] - buy['fee'] # Adjust the fee of the buy type to reflect the proportion of the amount that was sold
                    break # Go to the next sell type

                elif (diff <= 0): # If the buy amount is less than or equal to the sell amount: need to remove the buy from dataframe 
                    amt = buy['amount']
                    buy['cost_basis'] = buy['price'] * amt # Calculate the cost_basis of the buy type
                    sale['cost_basis'] = sale['price'] * amt # Calculate the cost_basis of the sell type
                    fee = sale['fee']
                    sale['fee'] = fee * (amt/sale['amount']) # Adjust the fee of the sell type proportionally to the amount of asset that was bought
                    sale['amount'] = amt # Update the amount of the sell type to match the amount bought in the buy type
                    pairs.append(list(sale) + list(buy)) # Add the sell and buy types to the list of pairs

                    df = df.drop(b) # Remove the buy type from the DataFrame since it has been fully used
                    buy_df = buy_df.drop(b) # Remove the buy type from the buy DataFrame since it has been fully used
                    sale['amount'] = abs(diff) # Update the amount of the sell type to reflect the remaining amount that was not sold
                    sale['fee'] = fee - sale['fee'] # Adjust the fee of the sell type to reflect the proportion of the amount that was bought

    pairs_df = pd.DataFrame.from_records(pairs) # Convert the list of pairs to a DataFrame
    pairs_df.columns = [col + ' (Sell)' for col in list(df.columns)] + [col + ' (Buy)' for col in list(df.columns)] # Rename the columns of the DataFrame to reflect the sell and buy types

    pairs_df['date (Sell)'] = [ts.strftime('%m-%d-%Y') for ts in pairs_df['date (Sell)']] # Convert the sell type dates to a readable format
    pairs_df['date (Buy)'] = [ts.strftime('%m-%d-%Y') for ts in pairs_df['date (Buy)']] # Convert the buy type dates to a readable format

    return pairs_df # Return the DataFrame of pairs
