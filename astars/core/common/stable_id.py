import hashlib


def generate_stable_id(
    *,
    type: str,
    start: int,
    end: int,
    parent_id: str | None,
) -> str:
    base = f"{type}:{start}:{end}"
    if parent_id:
        base += f":{parent_id}"

    return hashlib.sha1(base.encode()).hexdigest()
