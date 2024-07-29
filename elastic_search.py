import re 
import os
from elasticsearch import Elasticsearch

# Initialize Elasticsearch client

es = Elasticsearch(
    ['http://localhost:9200'],
    basic_auth=('elastic', os.getenv('ELASTIC_PASSWORD'))
    )

# Function to clean the name by removing trailing digits

def clean_name(name):
    return re.sub(r'\d+$', '', name)

# Function to search patient metadata

def patient_meta(q, size):
    response = es.search(
        index="patients_meta",
        body={
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["first", "last", "id"]
                }
            },
            "size": size
        }
    )
        # Extract and format search results

    results = [
        {
            "id": hit["_source"]["id"],
            "first": hit["_source"]["first"],
            "last": hit["_source"]["last"]
        }
        for hit in response["hits"]["hits"]
    ]
    return results

# Function to query Elasticsearch for specific patient data

def query_elasticsearch(patient_id, category):
    fields_to_include = []
    fields_to_exclude = ["patient_info.DEATHDATE", "patient.ID","patient_info.SSN", "patient_info.PASSPORT", "patient_info.RACE",
                "allergies.PATIENT", "allergies.ENCOUNTER", "careplans.ID", "careplans.PATIENT", "careplans.ENCOUNTER",
                "conditions.PATIENT", "conditions.ENCOUNTER", "encounters.ID", "encounters.PATIENT",
                "immunizations.PATIENT", "immunizations.ENCOUNTER", "medications.PATIENT", "medications.ENCOUNTER",
                "observations.PATIENT", "observations.ENCOUNTER", "procedures.PATIENT", "procedures.ENCOUNTER"
]

    category_fields = {
        "patient_info": "patient_info.*",
        "allergies": "allergies.*",
        "careplans": "careplans.*",
        "conditions": "conditions.*",
        "encounters": "encounters.*",
        "immunizations": "immunizations.*",
        "medications": "medications.*",
        "observations": "observations.*",
        "procedures": "procedures.*"
    }

    # Include specific fields based on the category

    if category in category_fields:
        fields_to_include.append(category_fields[category])

    query = {
        "_source": {
            "includes": fields_to_include,
            "excludes": fields_to_exclude
        },
        "query": {
            "term": {"_id": patient_id}
        }
    }

    response = es.search(index="patients", body=query)
    # print('===========================',response)
    if response['hits']['hits']:
        patient_data = response['hits']['hits'][0]['_source']
        # Clean first and last names

        if 'patient_info' in patient_data:
            if 'FIRST' in patient_data['patient_info']:
                patient_data['patient_info']['FIRST'] = clean_name(patient_data['patient_info']['FIRST'])
            if 'LAST' in patient_data['patient_info']:
                patient_data['patient_info']['LAST'] = clean_name(patient_data['patient_info']['LAST'])

        return patient_data
    else:
        return None

# Function to get recent patient information

def recent_info(patient_id):
    query = {
        "_source": {
            "includes": [
                "patient_info.*",
                "allergies.*",
                "careplans.*",
                "conditions.*",
                "encounters.*",
                "immunizations.*",
                "medications.*",
                "observations.*",
                "procedures.*"
            ],
            "excludes": [
                "patient_info.DEATHDATE", "patient.ID","patient_info.SSN", "patient_info.PASSPORT", "patient_info.RACE",
                "allergies.PATIENT", "allergies.ENCOUNTER", "careplans.ID", "careplans.PATIENT", "careplans.ENCOUNTER",
                "conditions.PATIENT", "conditions.ENCOUNTER", "encounters.ID", "encounters.PATIENT",
                "immunizations.PATIENT", "immunizations.ENCOUNTER", "medications.PATIENT", "medications.ENCOUNTER",
                "observations.PATIENT", "observations.ENCOUNTER", "procedures.PATIENT", "procedures.ENCOUNTER"
            ]
        },
        "query": {
            "term": {"_id": patient_id}
        }
    }
    response = es.search(index="patients", body=query)
     # Check if response contains patient data

    if response['hits']['hits']:
        patient_data = response['hits']['hits'][0]['_source']

        if 'patient_info' in patient_data:
            if 'FIRST' in patient_data['patient_info']:
                patient_data['patient_info']['FIRST'] = clean_name(patient_data['patient_info']['FIRST'])
            if 'LAST' in patient_data['patient_info']:
                patient_data['patient_info']['LAST'] = clean_name(patient_data['patient_info']['LAST'])

        # Extract the most recent records from each category
        recent_data = {'patient_info': patient_data['patient_info']}
        for category, date_field in {
            'allergies': 'START',
            'careplans': 'START',
            'conditions': 'START',
            'encounters': 'DATE',
            'immunizations': 'DATE',
            'medications': 'START',
            'observations': 'DATE',
            'procedures': 'DATE'
        }.items():
            if category in patient_data and patient_data[category]:
                sorted_records = sorted(patient_data[category], key=lambda x: x.get(date_field, ''), reverse=True)
                if sorted_records:
                    recent_data[category] = [sorted_records[0]]

        return recent_data
    else:
        return None


