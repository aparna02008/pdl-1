import sqlite3, csv

conn = sqlite3.connect("civisense.db")
cur = conn.execute("""
    select id,
           coalesce(nullif(issue_type, ''), reported_category) as category,
           reported_category, reported_severity,
           description, address, lat, lng, created_at
    from complaints
    order by id
""")

with open("to_label.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["complaint_id", "category", "reported_category", "reported_severity",
                "description", "address", "lat", "lng", "created_at",
                "severity", "priority"])
    n = 0
    for row in cur:
        w.writerow(list(row) + ["", ""])
        n += 1

print(f"Exported {n} complaints to to_label.csv")