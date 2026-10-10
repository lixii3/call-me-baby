from pathlib import Path


def path_esistente(valore: str) -> Path:
    p = Path(valore)
    if not p.exists():
        raise ValueError(f"Il percorso '{valore}' non esiste.")
    return p


def file_esistente(valore: str) -> Path:
    p = Path(valore)
    if not p.is_file():
        raise ValueError(f"'{valore}' non è un file valido.")
    return p