from dataclasses import dataclass
from typing import List
import pandas as pd
from .db import get_supabase

@dataclass
class BucketManager:
    supabase = get_supabase()

    def list(self) -> List[str]:
        res = self.supabase.table("baskets").select("slug").execute()
        return [r["slug"] for r in res.data]

    def members(self, slug: str) -> List[str]:
        res = self.supabase.table("basket_members").select("ticker").eq("slug", slug).execute()
        return [r["ticker"] for r in res.data]

    def add(self, slug: str, name: str, method: str="equal_weight"):
        self.supabase.table("baskets").upsert({"slug": slug, "name": name, "method": method}).execute()

    def add_member(self, slug: str, ticker: str, valid_from: str):
        self.supabase.table("basket_members").upsert(
            {"slug": slug, "ticker": ticker, "valid_from": valid_from}
        ).execute()

    def remove_member(self, slug: str, ticker: str, valid_from: str):
        self.supabase.table("basket_members").delete().match(
            {"slug": slug, "ticker": ticker, "valid_from": valid_from}
        ).execute()
