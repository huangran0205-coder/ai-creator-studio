import sqlite3
conn = sqlite3.connect(r'E:\Github_projet\BiliNote\backend\bili_note.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print('Table:', row[0])
    cursor.execute(f"SELECT * FROM {row[0]} LIMIT 3")
    rows = cursor.fetchall()
    if rows:
        cols = [d[0] for d in cursor.description]
        print('  Columns:', cols)
        for r in rows:
            print('  Data:', r)
conn.close()