import sqlite3

conn = sqlite3.connect("../eden_teacher.db")
cur = conn.cursor()
#cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
#[('knowledge_docs',), ('users',)]
#cur.execute("SELECT * FROM knowledge_docs")
#cur.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';")
#conn.commit()
#cur.execute("SELECT * FROM users")
cur.execute("SELECT * FROM knowledge_docs")
print(cur.fetchall())
conn.close()
