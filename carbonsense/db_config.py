import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ashish@2006",
    database="carbonsense1"
)

cursor = db.cursor(dictionary=True, buffered=True)