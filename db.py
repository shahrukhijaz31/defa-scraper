import requests
import pymysql

from lxml import html


# Example usage:
host = 'localhost'
user = 'root'
password = ''
database = 'defa_db'

connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    cursorclass=pymysql.cursors.DictCursor
)