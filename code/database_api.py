import sqlalchemy
import pandas as pd
from dateutil import parser

engine = sqlalchemy.create_engine("postgresql+psycopg2://postgres:password@localhost:5432/portfolio") # TODO: use configs for database URL

def read_transactions(include_id=True):

    table = pd.read_sql("""SELECT * FROM raw_transactions""", engine)
    if include_id:
        return table
    else:
        return table.drop(columns='id')

def enter_transactions(df):
    table = read_transactions(include_id=False)

    # correct dataframe to match SQL table # TODO: obviate lines 11-20 by editing read_data
    df.columns = [c.lower() for c in df.columns]
    df.rename(columns={'transaction': 'type',
                        'asset price': 'price',
                        'asset amount': 'amount',
                        'cost basis': 'cost_basis'},
                        inplace=True)
    df.drop(columns='payment', inplace=True)
    df = df.reindex(columns=['date', 'type', 'exchange', 'asset', 'price', 'amount', 'cost_basis', 'fee'])
    df['date'] = df['date'].apply(lambda x: x.replace(microsecond=0, tzinfo=None))
    df = df.apply(lambda col: round(col, 18) if col.dtype == 'float64' else col) # round numerics to 8 decimal places

    # drop duplicates rows only
    df = df.merge(table, how='left', indicator=True).pipe(lambda x: x.loc[x['_merge'] == 'left_only']).drop(columns='_merge')

    # insert dataframe into SQL
    df.to_sql('raw_transactions', 
              engine, 
              if_exists='append',
              index=False,
              dtype={'date': sqlalchemy.types.Date})
    
    return None
