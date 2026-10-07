"""
backup_restore.py — Backup and restore for heirbud.db.

Definition of Done #5 (docs/governance/HB-00_START_HERE.md) requires
"backups ... and tested recovery" before production. SQLite's own online
backup API (`sqlite3.Connection.backup`) is used so a backup can be taken
safely even while the server has the database open — it's a consistent
snapshot, not a raw file copy mid-write.

Usage:
    python backup_restore.py backup                 # -> backups/heirbud_TIMESTAMP.db
    python backup_restore.py restore backups/FILE.db # overwrites heirbud.db
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from heirbud_crm import DB_PATH

BACKUP_DIR = Path(__file__).parent / "backups"


def backup(db_path=DB_PATH, backup_dir: Path = BACKUP_DIR) -> str:
    """Take a consistent snapshot of ``db_path``. Returns the backup file path.

    Safe to call while the live database is open elsewhere — uses SQLite's
    backup API rather than copying the file bytes directly.
    """
    db_path = Path(db_path)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        raise FileNotFoundError(f"No database at {db_path} to back up.")
    dest = backup_dir / f"heirbud_{datetime.now():%Y%m%d_%H%M%S}.db"
    src_conn = sqlite3.connect(str(db_path))
    dest_conn = sqlite3.connect(str(dest))
    with dest_conn:
        src_conn.backup(dest_conn)
    src_conn.close()
    dest_conn.close()
    return str(dest)


def restore(backup_path, db_path=DB_PATH) -> str:
    """Restore ``db_path`` from a backup file. Returns the restored path.

    The current database, if any, is moved aside with a ``.pre-restore``
    suffix rather than deleted, so a bad restore is itself reversible.
    """
    backup_path = Path(backup_path)
    db_path = Path(db_path)
    if not backup_path.exists():
        raise FileNotFoundError(f"No backup at {backup_path}.")
    if db_path.exists():
        shutil.move(str(db_path), str(db_path) + ".pre-restore")
    shutil.copyfile(str(backup_path), str(db_path))
    return str(db_path)


def latest_backup(backup_dir: Path = BACKUP_DIR) -> str | None:
    files = sorted(Path(backup_dir).glob("heirbud_*.db"))
    return str(files[-1]) if files else None


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("backup", "restore"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "backup":
        print("Backed up to:", backup())
    else:
        if len(sys.argv) < 3:
            print("Usage: python backup_restore.py restore <path-to-backup.db>")
            sys.exit(1)
        print("Restored:", restore(sys.argv[2]))
