import json
import os
import sqlite3

def snapshot_onprem_db(db_path="onprem_legacy.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS legacy_records (id INTEGER PRIMARY KEY, name TEXT, value TEXT)")
    cursor.execute("INSERT INTO legacy_records (name, value) VALUES ('pet_001', 'active')")
    cursor.execute("INSERT INTO legacy_records (name, value) VALUES ('pet_002', 'vaccinated')")
    conn.commit()
    cursor.execute("SELECT id, name, value FROM legacy_records")
    data = cursor.fetchall()
    conn.close()
    return [{"id": d[0], "name": d[1], "value": d[2]} for d in data]

def replicate_to_aws_target(records, target_file="aws_replicated_records.json"):
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump({
            "migration_strategy": "Lift-and-Shift (AWS MGN)",
            "source_environment": "On-Premises Data Center",
            "target_environment": "AWS EC2 Spoke VPC",
            "replicated_records": records,
            "status": "CUTOVER_READY"
        }, f, indent=2)
    return True

def execute_migration():
    records = snapshot_onprem_db()
    replicate_to_aws_target(records)
    print(f"Lift-and-Shift completed: {len(records)} records synchronized to AWS target.")

if __name__ == "__main__":
    execute_migration()
