import pandas as pd
import numpy as np
from plotnine import *
from read_data import read_cashapp

df = read_cashapp('data/CashApp/cash_app_report.csv')

def clean_currency(x):
    """ If the value is a string, then remove currency symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(x, str):
        return(x.replace('$', '').replace(',', ''))
    return(x)
    
df['Asset Price'] = df['Asset Price'].apply(clean_currency).astype('float')

# Calculate Cost basis per transaction
df["Cost Basis"] = [x*y for (x, y) in zip(df["Asset Price"], df["Asset Amount"])]

get_costbasis(df, type="buys"):




def get_costbasis(df, asset='BTC'):
    """Calculate cost basis for an asset"""
    df = df[df['Asset'] == asset]
    buys_df = df[df["Transaction"] == "BUY"]
    sales_df = df[df["Transaction"] == "SALE"]

    total_asset_amount = sum(buys_df["Asset Amount"]) - sum(sales_df["Asset Amount"])
    cb_pershare = cost_basis / total_btc
    cost_basis / total_asset_amount
    # Adjust for sales in costbasis
    return(total_asset_amount)

df["Cost Basis"] = #
total_btc = sum(buys_df["Asset Amount"])
cost_basis = sum(buys_df["Amount"])

cb_pershare = cost_basis / total_btc

cb_pershare

#def get_costbasis(df, asset='BTC'):
#    """Calculate cost basis for an asset"""
#    df = df[df['Asset'] == asset]
#    buys_df = df[df["Transaction"] == "BUY"]
#    sales_df = df[df["Transaction"] == "SALE"]
#
#    total_asset_amount = sum(buys_df["Asset Amount"]) - sum(sales_df["Asset Amount"])
#    cb_pershare = cost_basis / total_btc
#    cost_basis / total_asset_amount
#    # Adjust for sales in costbasis
#    return(total_asset_amount)