from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
import re
from elasticsearch import Elasticsearch, helpers
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Replace with your actual database connection details
DATABASE = 'sqlite:///patients.db'
engine = create_engine(DATABASE)
metadata = MetaData()
metadata.reflect(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

def clean_name(name):
    if isinstance(name, str):
        return re.sub(r'\d+', '', name)
    return name

# Connect to Elasticsearch
es = Elasticsearch(
    ['http://localhost:9200'],
    basic_auth=('elastic', os.getenv('ELASTIC_PASSWORD'))
)

def fetch_related_data(query, params):
    result = session.execute(query, params).fetchall()
    return [dict(row._mapping) for row in result]

def fetch_patient_data(patient_id):
    patient_data = {}
    
    patient_info = session.execute(
        text("""SELECT BIRTHDATE, PREFIX, FIRST, LAST, MARITAL, GENDER, BIRTHPLACE, ADDRESS 
                FROM patients WHERE ID=:patient_id
             """),
        {"patient_id": patient_id}
    ).fetchone()

    if not patient_info:
        return None

    patient_data['info'] = dict(patient_info._mapping)
    patient_data['info']['PREFIX'] = clean_name(patient_data['info']['PREFIX'])
    patient_data['info']['FIRST'] = clean_name(patient_data['info']['FIRST'])
    patient_data['info']['LAST'] = clean_name(patient_data['info']['LAST'])

    patient_data['allergies'] = fetch_related_data(
        text("""SELECT *
                FROM allergies 
                WHERE PATIENT=:patient_id 
                """),
        {"patient_id": patient_id}
    )

    patient_data['careplans'] = fetch_related_data(
        text("""SELECT *
                FROM careplans 
                WHERE PATIENT=:patient_id
             """),
        {"patient_id": patient_id}
    )

    patient_data['conditions'] = fetch_related_data(
        text("""SELECT *
                FROM conditions 
                WHERE PATIENT=:patient_id
             """),
        {"patient_id": patient_id}
    )

    patient_data['encounters'] = fetch_related_data(
        text("""SELECT *
                FROM encounters 
                WHERE PATIENT=:patient_id
             """),
        {"patient_id": patient_id}
    )

    patient_data['immunizations'] = fetch_related_data(
        text("""SELECT *
                FROM immunizations 
                WHERE PATIENT=:patient_id
             """),
        {"patient_id": patient_id}
    )

    patient_data['medications'] = fetch_related_data(
        text("""SELECT *
                FROM medications 
                WHERE PATIENT=:patient_id
             """),
        {"patient_id": patient_id}
    )

    patient_data['observations'] = fetch_related_data(
        text("""SELECT *
                FROM observations 
                WHERE PATIENT=:patient_id
             """),
        {"patient_id": patient_id}
    )

    patient_data['procedures'] = fetch_related_data(
        text("""SELECT *
                FROM procedures 
                WHERE PATIENT=:patient_id
             """),
        {"patient_id": patient_id}
    )

    if not all(patient_data[category] for category in ['allergies', 'careplans', 'conditions', 'encounters', 'immunizations', 'medications', 'observations', 'procedures']):
        return None

    return patient_data

def transform_data(patient_id):
    patient_data = fetch_patient_data(patient_id)
    if patient_data:
        document = {
            "_index": "patients_full",
            "_id": patient_id,
            "_source": patient_data
        }
        return document
    return None

def bulk_import(data):
    helpers.bulk(es, data)

def log_patient_count(processed_count, total_count):
    print(f"Processed {processed_count}/{total_count} patients")

# Fetch patient IDs for the first 2000 patients and process in batches
batch_size = 2000
start_id = 0
total_processed = 0
total_to_process = 10000  # Specify the total number of patients you want to process

while total_processed < total_to_process:
    patient_ids = session.execute(text(f"SELECT ID FROM patients LIMIT {batch_size} OFFSET {start_id}")).fetchall()
    if not patient_ids:
        break  # No more patients to process
    patient_ids = [pid[0] for pid in patient_ids]

    # Transform data in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:  # Adjust number of workers based on your CPU
        future_to_patient_id = {executor.submit(transform_data, pid): pid for pid in patient_ids}
        transformed_data = []
        for future in as_completed(future_to_patient_id):
            try:
                data = future.result()
                if data:
                    transformed_data.append(data)
                total_processed += 1
                log_patient_count(total_processed, total_to_process)
            except Exception as exc:
                print(f'Patient ID {future_to_patient_id[future]} generated an exception: {exc}')

    # Bulk import transformed data
    bulk_import(transformed_data)

    # Move to the next batch
    start_id += batch_size
