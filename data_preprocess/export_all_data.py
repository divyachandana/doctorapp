import polars as pl
import os
import json
from elasticsearch import Elasticsearch, helpers
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


# Initialize Elasticsearch client
es = Elasticsearch(
    ['http://localhost:9200'],
    basic_auth=('elastic', os.getenv('ELASTIC_PASSWORD'))
)

folders = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
base_path = '../data_dump_sql/DATA/patient_1Million_csv'
files = ['patients', 'allergies', 'careplans', 'conditions', 'encounters', 'immunizations', 'medications', 'observations', 'procedures']

# Initialize empty DataFrames
df_patients = pl.DataFrame()
df_allergies = pl.DataFrame()
df_careplans = pl.DataFrame()
df_conditions = pl.DataFrame()
df_encounters = pl.DataFrame()
df_immunizations = pl.DataFrame()
df_medications = pl.DataFrame()
df_observations = pl.DataFrame()
df_procedures = pl.DataFrame()

# Define column data types for known issues
dtypes = {
    'VALUE': pl.Utf8
}

# Load all CSV files into DataFrames
for f in folders:
    for file in files:
        file_path = os.path.join(base_path, f, f"{file}.csv")
        print(f'Loading path: {file_path}')
        if os.path.exists(file_path):
            df = pl.read_csv(file_path, dtypes=dtypes, infer_schema_length=10000, ignore_errors=True)
            if file == 'patients':
                df_patients = df_patients.vstack(df) if not df_patients.is_empty() else df
            elif file == 'allergies':
                df_allergies = df_allergies.vstack(df) if not df_allergies.is_empty() else df
            elif file == 'careplans':
                df_careplans = df_careplans.vstack(df) if not df_careplans.is_empty() else df
            elif file == 'conditions':
                df_conditions = df_conditions.vstack(df) if not df_conditions.is_empty() else df
            elif file == 'encounters':
                df_encounters = df_encounters.vstack(df) if not df_encounters.is_empty() else df
            elif file == 'immunizations':
                df_immunizations = df_immunizations.vstack(df) if not df_immunizations.is_empty() else df
            elif file == 'medications':
                df_medications = df_medications.vstack(df) if not df_medications.is_empty() else df
            elif file == 'observations':
                df_observations = df_observations.vstack(df) if not df_observations.is_empty() else df
            elif file == 'procedures':
                df_procedures = df_procedures.vstack(df) if not df_procedures.is_empty() else df

def convert_to_dict(df, patient_id):
    if df.is_empty():
        return []
    else:
        return df.filter(pl.col('PATIENT') == patient_id).to_dicts()

def fetch_patient_data(patient_id):
    patient_info = df_patients.filter(pl.col('ID') == patient_id).to_dicts()[0]  # Assuming there's only one match
    allergies = convert_to_dict(df_allergies, patient_id)
    careplans = convert_to_dict(df_careplans, patient_id)
    conditions = convert_to_dict(df_conditions, patient_id)
    encounters = convert_to_dict(df_encounters, patient_id)
    immunizations = convert_to_dict(df_immunizations, patient_id)
    medications = convert_to_dict(df_medications, patient_id)
    observations = convert_to_dict(df_observations, patient_id)
    procedures = convert_to_dict(df_procedures, patient_id)

    patient_data = {
        "patient_info": patient_info,
        "allergies": allergies,
        "careplans": careplans,
        "conditions": conditions,
        "encounters": encounters,
        "immunizations": immunizations,
        "medications": medications,
        "observations": observations,
        "procedures": procedures
    }

    if not any(patient_data[category] for category in ['allergies', 'careplans', 'conditions', 'encounters', 'immunizations', 'medications', 'observations', 'procedures']):
        return None

    return patient_data

def transform_data(patient_id):
    patient_data = fetch_patient_data(patient_id)
    if patient_data:
        document = {
            "_index": "patients",
            "_id": patient_id,
            "_source": patient_data
        }
        return document
    return None

def bulk_import(data):
    try:
        helpers.bulk(es, data)
    except helpers.BulkIndexError as e:
        for error in e.errors:
            print(f"Failed to index document: {error}")

def log_patient_count(processed_count, total_count):
    print(f"Processed {processed_count}/{total_count} patients")

# Fetch patient IDs for the first 4000 patients and process in batches
total_time = 0
batch_size = 4000
start_id = 0
total_processed = 0
total_to_process = len(df_patients['ID'].unique())  # Specify the total number of patients you want to process

while total_processed < total_to_process:
    start_time = time.time()


    patient_ids = df_patients['ID'].unique()[start_id:start_id+batch_size]
    if patient_ids.is_empty():
        break  # No more patients to process

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
                print(f'Patient ID {future_to_patient_id[future]} generated an exception')

    # Bulk import transformed data
    if transformed_data:
        bulk_import(transformed_data)

        end_time = time.time() 
        batch_duration = end_time - start_time
        total_time += batch_duration
        print(f"Batch processed in {batch_duration:.2f} seconds")
        print(f"Cumulative total time: {total_time:.2f} seconds")

    # Move to the next batch
    start_id += batch_size

print(f"Total processing time: {total_time:.2f} seconds")
