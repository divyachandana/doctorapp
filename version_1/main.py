from typing import Union
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import httpx
import json
from model import fetch_patient_data, fetch_patient_category_data, prepare_prompt, prepare_category_prompt


app = FastAPI()


class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    print('--request--', request)
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "medllama2",
        "prompt": request.question,
        "stream": False
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(url, json=payload)
            print('response..', response)
            response.raise_for_status()
            result = response.json()
            answer = result["response"] if "response" in result else "No response"
            return QueryResponse(answer=answer)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    

@app.post("/askstream", response_model=QueryResponse)
async def ask_question_stream(request: QueryRequest):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": request.question,
        "stream": True
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                answer = ""
                # print(response.json())
                async for chunk in response.aiter_text():
                    for line in chunk.splitlines():
                        data = json.loads(line)
                        if "response" in data:
                            answer += data["response"]
                return QueryResponse(answer=answer)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


async def generate_summary(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        # "model": "medllama2",
        "prompt": prompt,
        "stream": False,
        "options": {
            # "num_keep": 5,
            "seed": 42,
            # "num_predict": 100,
            "top_k": 10,
            "top_p": 0.9,
            "tfs_z": 0.5,
            "typical_p": 0.7,
            "repeat_last_n": 33,
            "temperature": 0.8,
            "repeat_penalty": 1.2,
            "presence_penalty": 1.5,
            "frequency_penalty": 1.0,
            "mirostat": 1,
            "mirostat_tau": 0.8,
            "mirostat_eta": 0.6,
            # "penalize_newline": True,
            "stop": ["[\]", "user:"],
            "numa": False,
            # "num_ctx": 2048,
            "num_batch": 16,
            "num_gpu": 1,
            "main_gpu": 0,
            "low_vram": False,
            "f16_kv": True,
            "vocab_only": False,
            "use_mmap": True,
            "use_mlock": False,
            "num_thread": 20
        }
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            answer = result["response"] if "response" in result else "No response"
            tokens_per_second = result["eval_count"] / result["eval_duration"] * 1e9
            print("tokens_per_second", tokens_per_second)
            return answer
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@app.get("/patient_summary/{patient_id}", response_model=QueryResponse)
async def generate_patient_summary(patient_id: str):
    patient_data = fetch_patient_data(patient_id)
    if not patient_data['info']:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    prompt = prepare_prompt(patient_data)
    print('prompt', prompt)
    summary = await generate_summary(prompt)
    
    return QueryResponse(answer=summary)


@app.get("/patient_category_summary/{patient_id}/{category}", response_model=QueryResponse)
async def generate_patient_category_summary(patient_id: str, category: str):
    patient_category_data = fetch_patient_category_data(patient_id, category)
    if not patient_category_data.get(category):
        raise HTTPException(status_code=404, detail=f"No data found for category: {category}")
    
    prompt = prepare_category_prompt(patient_category_data, category)
    print(prompt)
    summary = await generate_summary(prompt)
    
    return QueryResponse(answer=summary)

async def generate_response(prompt):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                chunk_data = json.loads(chunk)
                if 'message' in chunk_data and 'content' in chunk_data['message']:
                    yield chunk_data['message']['content']

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            prompt = await websocket.receive_text()
            async for chunk in generate_response(prompt):
                await websocket.send_text(chunk)
    except WebSocketDisconnect:
        print("Client disconnected")

