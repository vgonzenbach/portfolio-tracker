import read_data
#import get_costbasis
import pandas as pd
from glob import glob

PROJECT_ROOT = '/Users/vgonzenb/projects/portfolio-tracker/'
exchange_paths = {'CashApp' : PROJECT_ROOT + 'data/CashApp/cash_app_report.csv',
                  'Coinbase' : PROJECT_ROOT + 'data/Coinbase/Basic/account.csv',
                  'Coinbase Pro' : PROJECT_ROOT + 'data/Coinbase/Pro/Default/fills.csv',
                  'Uniswap' : PROJECT_ROOT + 'data/Zerion/uniswap.csv',
                  'Fidelity': PROJECT_ROOT + 'data/Fidelity/*'}

def main():
    
    exchange_data = []
    for exchange, path in exchange_paths.items():
        df = read_data.read_data(path, exchange)
        exchange_data.append(df)

    df = pd.concat(exchange_data).sort_values(by='Date').reset_index(drop=True)

    # Use of different exchanges
    df['Exchange'].value_counts().plot(kind='bar')

    return df

if __name__ == '__main__':
    df = main()
    df.to_csv('output.csv')

