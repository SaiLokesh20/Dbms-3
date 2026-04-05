import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # username
        password="Sailok@1234",        # password
        database="CallHub"
    )