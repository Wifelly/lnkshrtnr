import sqlite3 as lite 
import sys

con = None

query_string = '''
    SELECT Urls.user_id, Urls.url, Urls.short_url, Urls.times_opened
    FROM Urls
    WHERE Urls.user_id = 'wifelly'
'''

try:
    con = lite.connect('db.db')
    cur = con.cursor()    
    cur.execute(query_string)
    con.commit()
    con.rollback()
    data = cur.fetchall()
    for item in data:
        print(item)
except Exception as e:
    print(e)
    sys.exit(1)
finally:
    if con is not None:
        con.close()