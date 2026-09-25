CONFIG = {
  'DataSource': {
    "timestamp_column": "close_time",
    "schema": {
      "open_time": "int",
      "open": "Decimal",
      "high": "Decimal",
      "low": "Decimal",
      "close": "Decimal",
      "volume": "Decimal",
      "close_time": "int",
      "quote_volume": "Decimal",
      "trades": "int",
      "taker_buy_base": "Decimal",
      "taker_buy_quote": "Decimal",
      "ignore": "int"
    },
    "CSVDataSource": {"delimiter": ","}
  }
}