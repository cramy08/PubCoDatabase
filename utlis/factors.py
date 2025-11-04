from .db import get_supabase

def ensure_factor(slug: str, name: str, category: str, method: str, meta: dict=None):
    sb = get_supabase()
    sb.table("factor_series").upsert({
        "slug": slug, "name": name, "category": category,
        "method": method, "meta": meta or {}
    }).execute()

def upsert_factor_values(slug: str, rows):
    # rows = [{"slug": slug, "dt": date, "level": x, "r_1d": r, "mean_r1d_252": m, ...}, ...]
    sb = get_supabase()
    # batch in chunks if needed
    sb.table("factor_values").upsert(rows).execute()
