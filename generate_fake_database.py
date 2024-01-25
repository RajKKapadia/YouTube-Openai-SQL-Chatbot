import re
from typing import Any
import json

import pandas as pd
from sqlalchemy import create_engine
import mysql.connector
from sqlalchemy_utils import database_exists, create_database
from faker import Faker
import pandas as pd

import config

faker = Faker()
Faker.seed(1234)

engine = create_engine(
    f'mysql+mysqlconnector://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DB_NAME}')


def clean_column_names(column_name: str) -> str:
    cleaned_name = column_name.replace(' ', '_')
    cleaned_name = re.sub(r'[^\w_]', '', cleaned_name)
    return cleaned_name


def is_valid_date(col: list) -> bool:
    date_string = str(col[0])
    patterns = [
        r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$',  # YYYY-MM-DD
        # DD-MMM-YYYY
        r'^(0[1-9]|[12][0-9]|3[01])-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}$',
        # MMM DD YYYY
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (0[1-9]|[12][0-9]|3[01]) \d{4}$',
        # YYYY-MMM-DD
        r'^\d{4}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(0[1-9]|[12][0-9]|3[01])$',
        # YYYY-MM-DD HH:MM:SS
        r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) (\d{2}):(\d{2}):(\d{2})$',
        # DD-MMM-YYYY HH:MM:SS
        r'^(0[1-9]|[12][0-9]|3[01])-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4} (\d{2}):(\d{2}):(\d{2})$',
        # MMM DD YYYY HH:MM:SS
        r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (0[1-9]|[12][0-9]|3[01]) \d{4} (\d{2}):(\d{2}):(\d{2})$',
        # YYYY-MMM-DD HH:MM:SS
        r'^\d{4}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(0[1-9]|[12][0-9]|3[01]) (\d{2}):(\d{2}):(\d{2})$',
        # DD-MM-YYYY HH:MM:SS
        r'^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-\d{4} (\d{2}):(\d{2}):(\d{2})$',
    ]
    for pattern in patterns:
        if re.match(pattern, date_string):
            return True
    return False


def convert_to_datetime(col: str) -> Any:
    try:
        if is_valid_date(col):
            return pd.to_datetime(col)
        return col
    except ValueError:
        return col


def get_column_names(cnx: mysql.connector.MySQLConnection, table_name: str) -> list[str]:
    """Return a list of column names."""
    cursor = cnx.cursor()
    column_names = []
    cursor.execute(
        f"SELECT * FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='{config.MYSQL_DB_NAME}' AND `TABLE_NAME`='{table_name}';")
    for col in cursor:
        column_names.append([col[3], col[7]])
    cursor.close()
    return column_names


print('Checking DB.')

if not database_exists(engine.url):
    create_database(engine.url)

print(f'DB exists - {database_exists(engine.url)}.')

cnx = mysql.connector.connect(user=config.MYSQL_USER, password=config.MYSQL_PASSWORD,
                              host=config.MYSQL_HOST, port=config.MYSQL_PORT, database=config.MYSQL_DB_NAME)

print('Reading CSV file.')

profiles = []
for _ in range(100):
    profiles.append(faker.profile())

data = pd.DataFrame.from_records(data=profiles)

print(data.columns)

data.drop(['current_location', 'website'], inplace=True, axis=1)

print('Cleaning CSV data.')

data.columns = [clean_column_names(col) for col in data.columns]

for col in data.columns:
    data[col] = convert_to_datetime(data[col])

print('Creating table and pushing the data.')

table_name = 'fake_profiles'
data.to_sql(table_name, engine, if_exists='replace',
            index=False, method='multi', chunksize=100)

print('Creating empty data definitions.')

data_definations = {
    "tables": [
        {
            "name": table_name,
            "description": "This table stores detailed user profiles.",
            "columns": []
        }
    ]
}

columns = get_column_names(cnx, table_name)

for column in columns:
    data_definations['tables'][0]['columns'].append(
        {
            "name": str(column[0]),
            "type": str(column[1]),
            "description": ""
        }
    )

print('Writing data definitions.')

with open('fake_data_definations.json', 'w') as file:
    file.write(json.dumps(data_definations, indent=2))

print('All is well.')