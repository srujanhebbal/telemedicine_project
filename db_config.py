import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Srujan@srujan1816",
        database="telemedicine_db"
    )