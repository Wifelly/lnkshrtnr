import sqlite3 as lite 
import sys

con = None

query_string = '''
  SELECT *
  FROM Urls
  ORDER BY url_id
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