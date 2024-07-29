import pandas as pd
from sqlalchemy import create_engine
from elasticsearch import Elasticsearch, helpers
import os
import re

# Connect to your SQLite database
DATABASE = 'sqlite:///patients.db'
engine = create_engine(DATABASE)

# Elasticsearch connection
es = Elasticsearch(
    ['http://localhost:9200'],
    basic_auth=('elastic', os.getenv('ELASTIC_PASSWORD'))
)
def clean_name(name):
    if isinstance(name, str):
        return re.sub(r'\d+', '', name)
    return name

def index_data_from_db():
    try:
        # Read specific columns from the patients table
        query = "SELECT ID, FIRST, LAST FROM patients"
        df = pd.read_sql_query(query, engine)
        print('Length of patients', len(df))
        # Prepare the data for Elasticsearch
        actions = [
            {
                "_index": "patients_meta",
                "_id": row["ID"],
                "_source": {
                    "id": row["ID"],
                    "first": clean_name(row["FIRST"]),
                    "last": clean_name(row["LAST"])
                }
            }
            for _, row in df.iterrows()
        ]

        # Bulk index data to Elasticsearch
        helpers.bulk(es, actions)
        print("Data indexed successfully.")
    except Exception as e:
        print(f"Error indexing data: {e}")

if __name__ == "__main__":
    index_data_from_db()
