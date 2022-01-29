import pandas as pd
from dateutil import parser

def read_cashapp(path):
    """Create transaction Data.Frame from CashApp .csv"""
    df = pd.DataFrame(columns = ["Date", "Exchange", "Transaction", "Asset", "Payment", "Asset Price", "Asset Amount"])
    
    cashapp_df = pd.read_csv(path)
    cashapp_df = cashapp_df[cashapp_df["Transaction Type"].isin(["Bitcoin Sale", "Bitcoin Buy"])]
    cashapp_df = cashapp_df.reset_index(drop=True)

    df['Date'] = [parser.parse(date) for date in cashapp_df["Date"]]
    df = df.assign(Exchange = 'CashApp') 

    def clean_transaction(record):
        if record == "Bitcoin Buy" :
            return("BUY")
        elif record == "Bitcoin Sale" :
            return("SALE")
    
    df['Transaction'] = list(cashapp_df["Transaction Type"].apply(clean_transaction).astype('str'))
    df['Asset'] = list(cashapp_df["Asset Type"])
    df['Payment'] = list(cashapp_df["Currency"])
    df["Asset Price"] = list(cashapp_df["Asset Price"])
    df["Asset Amount"] = list(cashapp_df["Asset Amount"])

    return(df)

def read_uniswap(path):
    """Create transaction Data.Frame from Zerion/Uniswap .csv"""
    df = pd.DataFrame(columns = ["Date", "Exchange", "Transaction", "Asset", "Payment", "Asset Price", "Asset Amount"])

    uniswap_df = pd.read_csv(path)
    uniswap_df = uniswap_df[uniswap_df["Transaction Type"] == 'Trade']
    uniswap_df = uniswap_df.reset_index(drop=True)

    # Get coins for calling CoinGecko API

    for index, row in uniswap_df.iterrows():
        """Create one buy and one sell row for each row in uniswap_df"""
        sell = {key: None for key in list(df.columns)}
        buy = {key: None for key in list(df.columns)}

        sell['Date'] = buy['Date'] = parser.parse(f'{row["Date"]} {row["Time"]}')
        sell['Exchange'] = buy['Exchange'] = "UniSwap"
        sell['Transaction'], buy['Transaction'] = 'SALE', 'BUY'
        sell['Asset'], buy['Asset'] = row['Sell Currency'], row['Buy Currency']
        sell['Payment'] = buy['Payment'] = 'USD'
        sell["Asset Price"], buy["Asset Price"] = row['Sell Fiat Amount'] / row['Sell Amount'], row['Buy Fiat Amount'] / row['Buy Amount']
        sell["Asset Amount"], buy["Asset Amount"] = row['Sell Amount'], row['Buy Amount']
        
        # Transfer data to Data.Frame
        df.loc[index*2] = sell
        df.loc[index*2 + 1] = buy

    return(df)

def read_coinbase(path):
    """Create transaction Data.Frame from Coinbase .csv"""
    df = pd.DataFrame(columns = ["Date", "Exchange", "Transaction", "Asset", "Payment", "Asset Price", "Asset Amount"])

    coinbase_df = pd.read_csv(path)
    coinbase_df = coinbase_df[coinbase_df["Transaction Type"].isin(["Buy", "Sell"])]
    coinbase_df = coinbase_df.reset_index(drop=True)

    df['Date'] = [parser.parse(date) for date in coinbase_df["Timestamp"]]
    df = df.assign(Exchange = 'Coinbase') 
    df['Transaction'] = coinbase_df['Transaction Type']
    df['Asset'] = coinbase_df['Asset']
    df['Payment'] = coinbase_df['Spot Price Currency']
    df['Asset Price'] = coinbase_df['Spot Price at Transaction']
    df['Asset Amount'] = coinbase_df['Quantity Transacted']

    return(df)