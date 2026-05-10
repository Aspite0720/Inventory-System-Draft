import mysql.connector

def get_connection():
    """Returns a connection to the MySQL database."""
    connection = mysql.connector.connect(
        host="localhost",        # Your MySQL server host
        user="root",             # Your MySQL username
        password="",# Your MySQL password
        database="Sari_Sari_Store"
    )
    return connection
