import sqlite3
def dump_db():
    conn = sqlite3.connect('backend/tipster.db')
    c = conn.cursor()
    print('--- SCHEMA ---')
    for row in c.execute("SELECT sql FROM sqlite_master WHERE type='table';").fetchall():
        if row[0]: print(row[0] + ';')
    print('\n--- TABLE COUNTS ---')
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    for t in tables:
        count = c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'{t}: {count} rows')
dump_db()
