import chromadb
import httpx
import json
import asyncio


client = chromadb.Client()


json_string = json.dumps(json_obj)

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


embedding = ollama_create_embedding(json_string)
collection.add(
    ids=["patietn_1"],
    embeddings=[embedding],
    documents=[json_string]
)

# ===========================================================================
# prompt = "What project Divya working on?"
prompt = "Provide patient recent summaary in all categories and provide any care plan suggestion"

prompt_embedding = ollama_create_embedding(prompt)
# ---------------------------------------------------------------------------

results = collection.query(
 query_embeddings=[prompt_embedding],
 n_results=1
)

data = results['documents'][0][0]

print(data)

# ===============================================================================
gen_prompt = f"you are health care assistant. using this data {data} respond to this prompt {prompt}"
output = asyncio.run(ollama_generate(gen_prompt))

print(output)











