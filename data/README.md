# Data Directory

Place your Cstore data files here:

## Recommended Files

- `sales_data.csv` or `sales_data.parquet` - Main sales transactions
- `products.csv` - Product catalog with categories
- `stores.csv` - Store location information
- `customers.csv` - Customer demographic data (if available)

## Data Format Examples

### Sales Data
```csv
date,store,product_name,category,quantity,sales_amount,payment_type
2024-01-01,Rigby,Coca Cola,Beverages,5,12.50,Credit
```

### Products
```csv
product_id,product_name,category,brand,unit_price
1,Coca Cola,Beverages,Coca-Cola Company,2.50
```

## Note

Currently, the app uses sample data for demonstration. Replace the `load_data()` functions in each page file with code to read your actual data files:

```python
@st.cache_data
def load_data():
    return pl.read_csv("data/sales_data.csv")
    # or for better performance:
    # return pl.read_parquet("data/sales_data.parquet")
```

## Parquet vs CSV

**Recommended**: Use Parquet format for better performance
- Faster read times (10-100x faster than CSV)
- Smaller file size (compressed)
- Preserves data types
- Better for large datasets

Convert CSV to Parquet:
```python
import polars as pl
df = pl.read_csv("sales_data.csv")
df.write_parquet("sales_data.parquet")
```
