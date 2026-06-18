import mysql.connector

con = mysql.connector.connect(
    host="localhost",
    user="root",
    password="rolls@mysql",
    database="school"
)

cur = con.cursor()
cur.execute("UPDATE marks SET marks=98 WHERE roll=33")
con.commit()
print("Record updated")

