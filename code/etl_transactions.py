import database_api
import read_data
import pandas as pd

PROJECT_ROOT = '/Users/vgonzenb/projects/portfolio-tracker/'
exchange_paths = {'CashApp' : PROJECT_ROOT + 'data/CashApp/cash_app_report.csv',
                  'Coinbase' : PROJECT_ROOT + 'data/Coinbase/Basic/account.csv',
                  'Coinbase Pro' : PROJECT_ROOT + 'data/Coinbase/Pro/Default/fills.csv',
                  'Uniswap' : PROJECT_ROOT + 'data/Zerion/uniswap.csv'}

def read_transactions(save_csv=True):
    """Extracts and transforms transaction data from .csv files into common format table"""
    exchange_data = []
    for exchange, path in exchange_paths.items():
        df = read_data.read_data(path, exchange)
        exchange_data.append(df)

    df = pd.concat(exchange_data).sort_values(by='Date').reset_index(drop=True)
    
    if save_csv:
        df.to_csv(PROJECT_ROOT + 'transactions.csv', index=False)

    return df


if __name__ == '__main__':
    df = read_transactions()
    database_api.enter_transactions(df)