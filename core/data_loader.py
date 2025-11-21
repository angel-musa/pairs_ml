import pandas as pd
from typing import List, Optional

def load_price_csv(path: str, date_col: str = "date", price_cols: Optional[List[str]] = None, index_col: Optional[str] = None) -> pd.DataFrame:
    """
    - Load CSV of prices.
    - Parse date_col or index_col to datetime and set as index.
    - Sort by index.
    - Assume business-day frequency and forward-fill missing values.
    - If price_cols is provided, keep only those columns; otherwise keep numeric columns.
    """
    # Read CSV
    df = pd.read_csv(path)
    
    # Handle index/date column
    if index_col:
        df[index_col] = pd.to_datetime(df[index_col])
        df.set_index(index_col, inplace=True)
    elif date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        df.set_index(date_col, inplace=True)
    else:
        # If neither is specified/found, assume index is already datetime-like or let user handle it?
        # The prompt implies we should parse date_col or index_col.
        pass

    # Sort by index
    df.sort_index(inplace=True)
    
    # Resample to business day and ffill
    # We assume the index is a DatetimeIndex now
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.asfreq('B')
        df.ffill(inplace=True)
    
    # Filter columns
    if price_cols:
        df = df[price_cols]
    else:
        # Keep numeric columns only
        df = df.select_dtypes(include=['number'])
        
    return df

def align_pairs(df: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    """
    - Return df[tickers] subset.
    - Drop any rows with NaNs.
    - Ensure index is sorted.
    """
    subset = df[tickers].copy()
    subset.dropna(inplace=True)
    subset.sort_index(inplace=True)
    return subset
