import pyodbc

def get_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=Butsee\SQLEXPRESS;'   # or just localhost
        'DATABASE=FaceAccessSystem;'
        'Trusted_Connection=yes;'         # uses Windows Authentication
    )
    return conn