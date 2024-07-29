import chromadb
import httpx
import json
import asyncio


client = chromadb.Client()

"""json_obj = {
        "_index": "patients_full",
        "_id": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
        "_score": 1,
        "_source": {
          "info": {
            "BIRTHDATE": "1946-08-02",
            "PREFIX": "Mr.",
            "FIRST": "Lorena",
            "LAST": "Simonis",
            "MARITAL": "M",
            "GENDER": "M",
            "BIRTHPLACE": "Newton MA US",
            "ADDRESS": "66970 Hoeger View Suite 349 Eastham MA 02642 US"
          },
          "allergies": [],
          "careplans": [
            {
              "ID": "f14963c4-9426-4e2a-9af8-20b70f54d49a",
              "START": "2001-07-20",
              "STOP": None,
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": 182964004,
              "DESCRIPTION": "Terminal care",
              "REASONCODE": 423121009,
              "REASONDESCRIPTION": "Non-small cell carcinoma of lung  TNM stage 4 (disorder)"
            },
            {
              "ID": "f14963c4-9426-4e2a-9af8-20b70f54d49a",
              "START": "2001-07-20",
              "STOP": None,
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": 133918004,
              "DESCRIPTION": "Comfort measures",
              "REASONCODE": 423121009,
              "REASONDESCRIPTION": "Non-small cell carcinoma of lung  TNM stage 4 (disorder)"
            },
            {
              "ID": "f14963c4-9426-4e2a-9af8-20b70f54d49a",
              "START": "2001-07-20",
              "STOP": None,
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": 408957008,
              "DESCRIPTION": "Chronic pain control management",
              "REASONCODE": 423121009,
              "REASONDESCRIPTION": "Non-small cell carcinoma of lung  TNM stage 4 (disorder)"
            },
            {
              "ID": "f14963c4-9426-4e2a-9af8-20b70f54d49a",
              "START": "2001-07-20",
              "STOP": None,
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": 243072006,
              "DESCRIPTION": "Cancer education",
              "REASONCODE": 423121009,
              "REASONDESCRIPTION": "Non-small cell carcinoma of lung  TNM stage 4 (disorder)"
            }
          ],
          "conditions": [
            {
              "START": "2001-07-02",
              "STOP": None,
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": 162573006,
              "DESCRIPTION": "Suspected lung cancer (situation)"
            },
            {
              "START": "2001-07-17",
              "STOP": None,
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": 254637007,
              "DESCRIPTION": "Non-small cell lung cancer (disorder)"
            },
            {
              "START": "2001-07-20",
              "STOP": None,
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": 423121009,
              "DESCRIPTION": "Non-small cell carcinoma of lung  TNM stage 4 (disorder)"
            }
          ],
          "encounters": [
            {
              "ID": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "DATE": "2002-01-26",
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "CODE": 308646001,
              "DESCRIPTION": "Death Certification",
              "REASONCODE": None,
              "REASONDESCRIPTION": None
            }
          ],
          "immunizations": [],
          "medications": [],
          "observations": [
            {
              "DATE": "2002-01-26",
              "PATIENT": "8e7dc04c-6c23-4d3c-8e4a-4e9996c9f299",
              "ENCOUNTER": "f7a4bc5b-e352-4b61-82e3-e8a7f1889c5d",
              "CODE": "254637007",
              "DESCRIPTION": "Non-small cell lung cancer (disorder)",
              "VALUE": None,
              "UNITS": None
            }
          ],
          "procedures": []
        }
      },
"""
json_obj = [{'id':1, 'name':'d', 'medications':[{'id':11, 'reason':'test1'}], 'allergy':[{'id':111,'reason':'peanut','date':"2024-01-01" }]},
            {'id':2, 'name':'d', 'medications':[{'id':12, 'reason':'test2'}], 'allergy':[{'id':111,'reason':'peanut','date':"2024-01-01" }]},
            {'id':3, 'name':'d', 'medications':[{'id':13, 'reason':'test3'}], 'allergy':[{'id':111,'reason':'peanut','date':"2024-01-01" }]}]
json_str = [json.dumps(data) for data in json_obj]
# json_string = json.dumps(json_obj)

collection = client.create_collection(name="test") #use persist for storage



embedding_model = 'mxbai-embed-large'
generate_model = "llama3"
API_URL = "http://localhost:11434/api/embeddings"
API_URL_gen = "http://localhost:11434/api/generate"
# -------------------------------------------------------------------

def ollama_create_embedding(prompt):
    payload = {
        "model": embedding_model,
        "prompt": prompt
    }
    response = httpx.post(API_URL, json=payload)
    return response.json().get("embedding")    


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
# ----------------------------------------------------------------------

for i, json_string in enumerate(json_str):
  embedding = ollama_create_embedding(json_string)
  collection.add(
      ids=[str(i)],
      embeddings=[embedding],
      documents=[json_string],
      # metadata=[{"patient_id": json_obj[i]["id"]}]
  )

# ===========================================================================
# prompt = "What project Divya working on?"
prompt = "get patient id 1 data"

prompt_embedding = ollama_create_embedding(prompt)
# ---------------------------------------------------------------------------

results = collection.query(
 query_embeddings=[prompt_embedding],
 n_results=1
)

data = results['documents'][0][0]

print(data)

# ===============================================================================
gen_prompt = f"you are health care assistant. using this data {data} respond to this prompt {prompt} get only allergy info"
output = asyncio.run(ollama_generate(gen_prompt))

print(output)











