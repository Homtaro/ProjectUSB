import string

def clean_serial(value: str | None) -> str:
    if not value or not isinstance(value, str):
        return "—"

    cleaned = "".join(c for c in value if c in string.printable).strip()

    if len(cleaned) < 4 or cleaned.count("0") == len(cleaned):
        return "Unavailable"

    return cleaned

def shorten_pnp_id(pnp: str | None, max_len: int = 48) -> str:
    if not pnp:
        return "—"

    if len(pnp) <= max_len:
        return pnp

    return pnp[:max_len - 1] + "…"
