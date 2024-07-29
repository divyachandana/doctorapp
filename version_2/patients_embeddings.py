import polars as pl
import os
import json
import chromadb
import httpx
import asyncio

client = chromadb.Client()
collection = client.create_collection(name="patients")

embedding_model = 'mxbai-embed-large'
generate_model = "llama3"
API_URL = "http://localhost:11434/api/embeddings"
API_URL_gen = "http://localhost:11434/api/generate"

def ollama_create_embedding(prompt):
    payload = {
        "model": embedding_model,
        "prompt": prompt
    }
    response = httpx.post(API_URL, json=payload)
    embedding = response.json().get("embedding")
    # print(f"Created embedding for prompt: {prompt[:30]}...")  # Debugging print
    return embedding

async def ollama_generate(p):
    payload = {
        "model": generate_model,
        "prompt": p,
        "stream": False
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(API_URL_gen, json=payload)
            return response.json().get("response")
    except Exception as e:
        print(e)

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

count = 0
pat = ''
print('Total unique patient IDs:', len(df_patients['ID'].unique()))
for patient_id in df_patients['ID'].unique()[:100]:
    print(f'Processing patient ID: {patient_id}')
    patient_info = df_patients.filter(pl.col('ID') == patient_id).to_dicts()[0]  # Assuming there's only one match

    allergies = convert_to_dict(df_allergies, patient_id)
    careplans = convert_to_dict(df_careplans, patient_id)
    conditions = convert_to_dict(df_conditions, patient_id)
    encounters = convert_to_dict(df_encounters, patient_id)
    immunizations = convert_to_dict(df_immunizations, patient_id)
    medications = convert_to_dict(df_medications, patient_id)
    observations = convert_to_dict(df_observations, patient_id)
    procedures = convert_to_dict(df_procedures, patient_id)

    if not (allergies or careplans or conditions or encounters or immunizations or medications or observations or procedures):
        continue

    count += 1
    print(f'Processed {count} patients so far')
    patient_json = {
        "id": patient_id,
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
    pat = patient_id

    embedding = ollama_create_embedding(json.dumps(patient_json))
    # print(f'Embedding created for patient ID: {patient_id}')
    collection.add(
        ids=[str(count)],
        embeddings=[embedding],
        documents=[json.dumps(patient_json)]
    )

id = 90
print('Last processed patient ID:', pat)

# Perform a similarity query
prompt = f"patient_id {id}"
prompt_embedding = ollama_create_embedding(prompt)
# print(f'Prompt embedding created for ID: {id}')

results = collection.query(
    query_embeddings=[prompt_embedding],
    n_results=1,  # Retrieve more results to increase chances of consistency
    # where={"id": {"$eq": str(id)}}
)

# print(f'Query results: {results}')

data = results['documents'][0][0] if results['documents'][0] else None
print(f'Queried data for ID {id}: {data}')

gen_prompt = f"you are health care assistant. using this data {data} respond to this prompt {prompt} get only observations info"
output = asyncio.run(ollama_generate(gen_prompt))

print(f'Generated response: {output}')

