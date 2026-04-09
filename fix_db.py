import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='hms_user',
    password='abcdallusirish',
    database='hms_db'
)
try:
    cursor = conn.cursor()
    cursor.execute("UPDATE Users SET password_hash = %s", ('$2b$12$wvRDZl/ujIWrzYq734phgl3OuH6X5m42wk8VNQ7UQTtwdkh',))
    conn.commit()
    print("DB FIXED")
finally:
    conn.close()
