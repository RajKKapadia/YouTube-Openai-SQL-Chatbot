import decimal
import json
import datetime

import mysql.connector

import config

cnx = mysql.connector.connect(user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
                              host=config.MYSQL_HOST, port=config.MYSQL_PORT, database=config.MYSQL_DB_NAME)


def get_table_names(cnx: mysql.connector.MySQLConnection) -> list[str]:
    """Return a list of table names."""
    cursor = cnx.cursor()
    table_names = []
    cursor.execute(
        f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{config.MYSQL_DB_NAME}';")
    for table in cursor:
        if table[0] in config.MYSQL_TABLES:
            table_names.append(table[0])
    cursor.close()

    return table_names


def get_column_names(cnx: mysql.connector.MySQLConnection, table_name: str) -> list[str]:
    """Return a list of column names."""
    cursor = cnx.cursor()
    column_names = []
    cursor.execute(
        f"SELECT `COLUMN_NAME` FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='{config.MYSQL_DB_NAME}' AND `TABLE_NAME`='{table_name}';")
    for col in cursor:
        column_names.append(col[0])
    cursor.close()

    return column_names


def get_database_info(cnx: mysql.connector.MySQLConnection) -> dict:
    """Return a list of dicts containing the table name and columns for each table in the database."""
    cursor = cnx.cursor()
    table_dicts = []
    for table_name in get_table_names(cnx):
        columns_names = get_column_names(cnx, table_name)
        table_dicts.append(
            {"table_name": table_name, "column_names": columns_names})
    cursor.close()

    return table_dicts


database_schema_dict = get_database_info(cnx)

database_schema_string = "\n".join(
    [
        f"Table: {table['table_name']}\nColumns: {', '.join(table['column_names'])}"
        for table in database_schema_dict
    ]
)

database_definitions = {}
with open('fake_data_definations.json', 'r') as file:
    database_definitions = json.loads(file.read())


def format_number(amount):
    def truncate_float(number, places):
        return int(number * (10 ** places)) / 10 ** places
    if amount < 1e3:
        return amount
    if 1e3 <= amount < 1e5:
        return str(truncate_float((amount / 1e5) * 100, 2)) + " K"
    if 1e5 <= amount < 1e7:
        return str(truncate_float((amount / 1e7) * 100, 2)) + " L"
    if amount > 1e7:
        return str(truncate_float(amount / 1e7, 2)) + " Cr"


def serialize_data(obj) -> str:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return format_number(float(obj))
    raise TypeError(f"Object type not serializable - {type(obj)}")


def ask_database(cnx: mysql.connector.MySQLConnection, query: str):
    """Function to query SQLite database with a provided SQL query."""
    try:
        cursor = cnx.cursor(dictionary=True)
        cursor.execute(query)
        results = ''
        for data in cursor:
            print(data)
            results += json.dumps(data, default=serialize_data)
    except Exception as e:
        print(e.args[0])
    else:
        pass

    return results


def execute_function_call(query: str) -> str:
    results = ask_database(cnx, query)
    print(results)

    return results
