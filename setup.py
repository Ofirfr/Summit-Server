# This file is for creating the sql tables and setting up an admin user
import bcrypt
import psycopg2
import hashlib
import sys


# Connect to db
con = psycopg2.connect(
    host = 'db',
    user = 'postgres',
    password = 'password',
    port = '5432',
    database = 'SummitDB'
)

# Create all needed tables and sequnces in the data base
def createTables():
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE Training_Table
        (
            ID SERIAL PRIMARY KEY,
            coach TEXT NOT NULL,
            date TEXT NOT NULL,
            PERSON TEXT NOT NULL
        )
        """
    )
    con.commit()
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE Person_Table
        (
            ID SERIAL PRIMARY KEY,
            f_name TEXT NOT NULL,
            l_name TEXT NOT NULL,
            training TEXT NOT NULL
        )
        """
    )
    con.commit()

    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE USER_Table
        (
            USERNAME TEXT  NOT NULL,
            PASSWORD TEXT  NOT NULL
        )
        """
    )
    con.commit()

    #Set up AUTO INCREMENT
    cur = con.cursor()
    cur.execute(
        """
        CREATE SEQUENCE Training_sequence
            start 1
            increment 1;
        """
    )

    con.commit()
    cur.execute(
        """
        CREATE SEQUENCE Person_sequence
            start 1
            increment 1;
        """
    )
    
    con.commit()

# Create an admin user with input password 
def createAdmin():
    if len(sys.argv)==0:
        return
    password = sys.argv[1]
    password = hashlib.sha512(password.encode("utf-8")).hexdigest()
    password = bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
    cur = con.cursor()
    cur.execute(
    f"""
    INSERT INTO USER_Table 
    (USERNAME,PASSWORD)
    VALUES('admin','{password}')
    """ 
    )
    print("Created admin with given password")
    con.commit()
    con.close()


def checkToSetup():
    # Check if user_table exist (if it does, all tables exist)
    cur = con.cursor()
    cur.execute(
        """
        SELECT EXISTS (
        SELECT FROM pg_tables
        WHERE tablename  = 'user_table'
        );
        """
    )
    data = cur.fetchall()
    tablesCreated = data[0][0]
    # Return False = tables not created = need to setup
    if not tablesCreated:
        return False
    print("Tables already created, not creating admin with given password.")
    return True