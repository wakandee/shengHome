import MySQLdb  # or import pymysql

def check_and_create_db(db_name):
    """Check if the database exists and create it if not."""
    connection = MySQLdb.connect(host="localhost", user="root", password="admin")
    cursor = connection.cursor()

    # Check if the database exists
    cursor.execute("SHOW DATABASES LIKE '%s';" % db_name)
    result = cursor.fetchone()

    if not result:
        # If the database doesn't exist, create it
        cursor.execute(f"CREATE DATABASE {db_name};")
        print(f"Database {db_name} created!")
    else:
        print(f"Database {db_name} already exists.")

    # Close the connection
    cursor.close()
    connection.close()
