import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_ANON_KEY"]

sb = create_client(url, key)

# Try a lightweight query against the table we created
r = sb.table("prices_daily").select("ticker").limit(1).execute()
print("OK: connected. Sample response length:", len(r.data))
