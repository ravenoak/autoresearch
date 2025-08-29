# Storage Backup

Consistent backups ensure that restored databases reproduce the original
state. DuckDB checkpoints flush pending writes, after which copying the
database file captures a stable snapshot. The script
[storage_backup_sim.py](../../scripts/storage_backup_sim.py) builds a
database, issues `CHECKPOINT`, copies the file, and compares sorted rows
from source and backup.

Proof. For any finite table contents inserted before the checkpoint,
copying the database file yields a target whose query results match the
source. Since the simulation observes equality of all rows, the backup is
consistent. Thus a restore from the backup replays the exact original data.
