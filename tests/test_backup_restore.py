"""Prove the recovery path actually works: back up, lose the DB, restore, data's still there."""
import backup_restore
from heirbud_crm import HeirBudCRM


def test_backup_then_restore_recovers_data(tmp_path):
    db_path = tmp_path / "live.db"
    crm = HeirBudCRM(db_path=db_path)
    crm.add_prospect({"property_id": "B-1", "name": "Backup Test",
                      "amount": 12345, "holder": "EXAMPLE BANK",
                      "last_known_address": "1 Test St, Madison, WI"})

    backup_dir = tmp_path / "backups"
    backup_path = backup_restore.backup(db_path=db_path, backup_dir=backup_dir)
    assert backup_path

    # Simulate total loss of the live database.
    db_path.unlink()
    assert not db_path.exists()

    restored_path = backup_restore.restore(backup_path, db_path=db_path)
    assert restored_path == str(db_path)

    recovered = HeirBudCRM(db_path=db_path)
    p = recovered.get_prospect("B-1")
    assert p is not None
    assert p["name"] == "Backup Test"
    assert p["amount"] == 12345


def test_restore_keeps_the_old_file_instead_of_deleting_it(tmp_path):
    db_path = tmp_path / "live.db"
    crm = HeirBudCRM(db_path=db_path)
    crm.add_prospect({"property_id": "B-2", "name": "Original", "amount": 1,
                      "last_known_address": "1 Test St, Madison, WI"})
    backup_dir = tmp_path / "backups"
    backup_path = backup_restore.backup(db_path=db_path, backup_dir=backup_dir)

    # Corrupt the "live" DB with different data, then restore over it.
    crm.add_prospect({"property_id": "B-3", "name": "Should be gone after restore",
                      "amount": 2, "last_known_address": "1 Test St, Madison, WI"})
    backup_restore.restore(backup_path, db_path=db_path)

    assert (tmp_path / "live.db.pre-restore").exists()  # old file moved aside, not deleted
    recovered = HeirBudCRM(db_path=db_path)
    assert recovered.get_prospect("B-2") is not None
    assert recovered.get_prospect("B-3") is None


def test_backup_refuses_missing_database(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        backup_restore.backup(db_path=tmp_path / "nope.db", backup_dir=tmp_path / "backups")
