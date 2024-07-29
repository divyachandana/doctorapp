import chromadb
import httpx
import json
import asyncio


client = chromadb.Client()


collection = client.create_collection(name="test") #use persist for storage

documents = ["Divya is a software developer",
            "divya working on amd project its very interesting its a patient summary application with lof of interesting things going on",
             "divya like lot of things",
                "divya is moody", 
                "divya is active"]


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
doc_count = collection.count()

if doc_count > 0:
    print(f"There are {doc_count} documents in the collection.")
else:
    print("The collection is empty.")

    for i, d in enumerate(documents):
        embedding = ollama_create_embedding(d)
        collection.add(
            ids=[str(i)],
            embeddings=[embedding],
            documents=[d]
        )

# ===========================================================================
# prompt = "What project Divya working on?"
prompt = "how Divyas mental state?"

prompt_embedding = ollama_create_embedding(prompt)
# ---------------------------------------------------------------------------

results = collection.query(
 query_embeddings=[prompt_embedding],
 n_results=1
)

data = results['documents'][0][0]

print(data)

# ===============================================================================
gen_prompt = f"using this data {data} respond to this prompt {prompt}"
output = asyncio.run(ollama_generate(gen_prompt))

print(output)











