import sqlite3
from pathlib import Path


SOURCE_DB = Path("/source/financial_manager.db")
TARGET_DB = Path("/data/financial_manager.db")


def main():
    if TARGET_DB.exists():
        print("O banco do volume já existe; mantendo os dados do Docker.", flush=True)
        return
    if not SOURCE_DB.is_file():
        print("Banco local não encontrado; o app criará um banco novo no volume.", flush=True)
        return

    TARGET_DB.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    target = sqlite3.connect(TARGET_DB)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    print("Banco local copiado para o volume persistente do Docker.", flush=True)


if __name__ == "__main__":
    main()
