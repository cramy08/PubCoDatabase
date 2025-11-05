from tiingo import TiingoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = TiingoClient({'api_key': os.getenv("TIINGO_TOKEN")})

for ticker in ['BIO','MTD','WAT','BRKR','ILMN','NCR','SQ','TMO']:  # replace with missing tickers
    try:
        prices = client.get_dataframe(ticker, startDate="2015-01-01")
        print(ticker, "✅", len(prices), "rows")
    except Exception as e:
        print(ticker, "❌", e)


