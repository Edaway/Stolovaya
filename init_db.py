import sqlite3

# Пути к файлам
db_file = "database.db"
sql_file = "database.sql"

# Читаем SQL из файла
with open(sql_file, "r", encoding="utf-8") as f:
    sql_script = f.read()

# Создаём базу и выполняем SQL
conn = sqlite3.connect(db_file)
cur = conn.cursor()
cur.executescript(sql_script)
conn.commit()
conn.close()

print("База данных создана и заполнена!")
