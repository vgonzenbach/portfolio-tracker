import pandas as pd
from dateutil import parser
from pycoingecko import CoinGeckoAPI
from glob import glob

cg = CoinGeckoAPI()

def get_coin_id(symbol):
    """Returns id for a given symbol via CoinGecko API"""
    # Find match for symbol in CoinGecko coins list
    coins = cg.get_coins()
    coin = [coin for coin in coins if symbol.lower() == coin['symbol']].pop()  # Take first match
    return(coin['id'])

def get_price_at_date(symbol, date):
    history = cg.get_coin_history_by_id(id=get_coin_id(symbol), date=date.strftime('%d-%m-%Y'))
    price = history['market_data']['current_price']['usd']
    return(price)

def read_cashapp(path):
    """Create transaction Data.Frame from CashApp .csv"""
    df = pd.DataFrame(columns = ["Date", "Exchange", "Transaction", "Asset", "Payment", "Asset Price", "Asset Amount"])
    
    cashapp_df = pd.read_csv(path)
    cashapp_df = cashapp_df[cashapp_df["Transaction Type"].isin(["Bitcoin Sale", "Bitcoin Buy"])]
    cashapp_df = cashapp_df.reset_index(drop=True)

    df['Date'] = [parser.parse(date) for date in cashapp_df["Date"]]
    df = df.assign(Exchange = 'CashApp') 

    def clean_currency(x):
        """ If the value is a string, then remove currency symbol and delimiters
        otherwise, the value is numeric and can be converted
        """
        if isinstance(x, str):
            return(x.replace('$', '').replace(',', ''))
        return(x)
    
    def clean_transaction(record):
        if record == "Bitcoin Buy" :
            return("BUY")
        elif record == "Bitcoin Sale" :
            return("SALE")
    
    df['Transaction'] = cashapp_df["Transaction Type"].apply(clean_transaction).astype('str')
    df['Asset'] = cashapp_df["Asset Type"]
    df['Payment'] = cashapp_df["Currency"]
    df["Asset Price"] = list(map(clean_currency, cashapp_df["Asset Price"]))
    df["Asset Amount"] = cashapp_df["Asset Amount"]

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
        sell['Exchange'] = buy['Exchange'] = "Uniswap"
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
    """Create transaction Data.Frame from Coinbase .csv file"""
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

def read_coinbasepro(path):
    """Create transaction Data.Frame from Coinbase Pro .csv file"""
    df = pd.DataFrame(columns = ["Date", "Exchange", "Transaction", "Asset", "Payment", "Asset Price", "Asset Amount"])

    coinbase_df = pd.read_csv(path)

    records = []
    for index, row in coinbase_df.iterrows():
        record = {key: None for key in list(df.columns)}
        
        if row['price/fee/total unit'] == 'USD':
            record['Date'] = parser.parse(row["created at"])
            record['Transaction'] = row['side']
            record['Asset'] = row['size unit']
            record['Payment'] = 'USD'
            record['Asset Price'] = row['price']
            record['Asset Amount'] = row['size']

        else:
            # Record2 identifies the underlying asset
            record2 = {key: None for key in list(df.columns)}
            record['Date'] = record2['Date'] = parser.parse(row["created at"])
            record['Transaction'] = row['side']
            record2['Transaction'] = {'BUY', 'SELL'}.difference({record['Transaction']}).pop() # Take complement 
            record['Asset'], record2['Asset'] = row['size unit'], row['price/fee/total unit']
            record['Payment'] = record2['Payment'] = 'USD'
            record2['Asset Price'] = get_price_at_date(symbol=row['price/fee/total unit'], date=record['Date'])
            record['Asset Price'] = record2['Asset Price']*row['price']
            record['Asset Amount'], record2['Asset Amount'] = row['size'], row['price']
            records.append(record2)
        records.append(record)
    
    for i, rec in enumerate(records):
        df.loc[i] = rec
    df = df.assign(Exchange = 'Coinbase Pro')
    return(df)

def read_fidelity(path):
    """Reads in data from quarters Fidelity"""
    df = pd.DataFrame(columns = ["Date", "Exchange", "Transaction", "Asset", "Payment", "Asset Price", "Asset Amount"])
    
    paths = glob(path)
    df_list = [pd.read_csv(path, header=1) for path in paths]
    fidelity_df = pd.concat(df_list).reset_index()

    transaction_filter = [x & y for x, y in zip(fidelity_df['Symbol'] != ' ', pd.notna(fidelity_df['Symbol']))]
    fidelity_df = fidelity_df.loc[transaction_filter]
    
    df['Date'] = [parser.parse(date) for date in fidelity_df['Run Date']]
    df['Exchange'] = 'Fidelity'
    df['Transaction'] = ['SELL' if quant < 0 else 'BUY' for quant in fidelity_df['Quantity']]
    df['Asset'] = fidelity_df['Symbol']
    df['Payment'] = 'USD'
    df['Asset Price'] = fidelity_df['Price ($)']
    df['Asset Amount'] = abs(fidelity_df['Amount ($)'])

    return(df)
    
def read_data(path, exchange):
    """Wrapper for exchange data readers"""

    if exchange == 'Coinbase Pro':
        df = read_coinbasepro(path)
    
    elif exchange == 'Coinbase':
        df = read_coinbase(path)
    
    elif exchange == 'Uniswap':
        df = read_uniswap(path)
    
    elif exchange == 'CashApp':
        df = read_cashapp(path)
    
    elif exchange == 'Fidelity':
        df = read_fidelity(path)
    
    return(df)
