import mysql.connector

def conect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="senai",
        database="pwbe_escola"
    )