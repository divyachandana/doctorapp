from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

import httpx
import json
from prompt import Augment
import wandb
from gpu_metrics import get_gpu_metrics

app = FastAPI()
from elastic_search import query_elasticsearch, recent_info, patient_meta



# Initialize Weights & Biases
wandb.init(project="patient-summary", entity="divyachandana-audigent")

# Allowed origins for CORS

origins = [
    "http://localhost",
    "http://localhost:3000",
]
# Add CORS middleware to allow specified origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

# Asynchronous function to generate a response from the LLM API

async def generate_response(prompt):
    url = "http://localhost:11434/api/chat"
    payload = {
        # "model": "llama3",
        # "model": "medllama2",
        "model": "llama3.1",

        "messages": [
            {
                "role": "system",
                "content": "You are a helpful medical assistant. Your responses should be accurate, brief, and related to healthcare and medical topics."
            },
            {
                "role": "user",
                "content": f"{prompt}"
            }
        ],
        "stream": True,
    }
    # Make an asynchronous POST request to the LLM API

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
        try:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    chunk_data = json.loads(chunk)
                    if 'message' in chunk_data and 'content' in chunk_data['message']:
                        yield chunk_data['message']['content']

        except Exception as e:
            print(f"Inference request failed: {e}")
# Log final metrics if the response is complete
    if 'done' in chunk_data and chunk_data['done']:
        eval = (chunk_data['eval_duration'] / 1e9)
        tokens_per_second = chunk_data['eval_count'] / eval  # eval_duration is in nanoseconds

        gpu_utilization, gpu_temp, vram_usage, fan_speed, power_cap, mem_usage = get_gpu_metrics()

        # Log final metrics to Weights & Biases
        final_log_data = {
            "chat_tokens_per_second": tokens_per_second,
            "chat_gpu_utilization": gpu_utilization,
            "chat_gpu_temp": gpu_temp,
            "chat_vram_usage": vram_usage,
            "chat_fan_speed": fan_speed,
            "chat_power_cap": power_cap,
            "chat_mem_usage": mem_usage,
            "chat_total_duration_seconds": chunk_data['total_duration']/ 1e9,
            "chat_load_duration_seconds": chunk_data['load_duration']/ 1e9,
            "chat_prompt_eval_count": chunk_data['prompt_eval_count'],
            "chat_prompt_eval_duration_seconds": chunk_data['prompt_eval_duration']/ 1e9,
            "chat_eval_count": chunk_data['eval_count'],
            "chat_eval_duration_seconds": chunk_data['eval_duration']/ 1e9
        }
        try:
            wandb.log(final_log_data)
        except wandb.errors.CommError as e:
            print(f"Error logging to Weights & Biases: {e}")

# WebSocket endpoint for real-time communication with the client

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            prompt = await websocket.receive_text()
            print(f"Received from client: {prompt}")
            async for chunk in generate_response(prompt):
                await websocket.send_text(chunk)
                # print(f"Sent to client: {chunk}")
    except WebSocketDisconnect:
        print("Client disconnected")

# Asynchronous function to generate a summary from the LLM API

async def generate_summary(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        # "model" : "meditron",
        # "model" : "medllama2",
        # "model": "llama3",
        "model": "llama3.1",
        # "model": "llama3.1:70b-instruct-q4_0",
        "prompt": prompt,
        "stream": True,
    }
    # Make an asynchronous POST request to the LLM API

    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
        try:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    chunk_data = json.loads(chunk)
                    if 'response' in chunk_data:
                        yield chunk_data['response']

        except Exception as e:
            print(f"Inference request failed: {e}")

    # Log final metrics if the response is complete

    if 'done' in chunk_data and chunk_data['done']:
        eval = (chunk_data['eval_duration'] / 1e9)
        tokens_per_second = chunk_data['eval_count'] / eval  # eval_duration is in nanoseconds

        gpu_utilization, gpu_temp, vram_usage, fan_speed, power_cap, mem_usage = get_gpu_metrics()

        # Log final metrics to Weights & Biases
        final_log_data = {
            "tokens_per_second": tokens_per_second,
            "gpu_utilization": gpu_utilization,
            "gpu_temp": gpu_temp,
            "vram_usage": vram_usage,
            "fan_speed": fan_speed,
            "power_cap": power_cap,
            "mem_usage": mem_usage,
            "total_duration_seconds": chunk_data['total_duration']/ 1e9,
            "load_duration_seconds": chunk_data['load_duration']/ 1e9,
            "prompt_eval_count": chunk_data['prompt_eval_count'],
            "prompt_eval_duration_seconds": chunk_data['prompt_eval_duration']/ 1e9,
            "eval_count": chunk_data['eval_count'],
            "eval_duration_seconds": chunk_data['eval_duration']/ 1e9
        }
        try:
            wandb.log(final_log_data)
        except wandb.errors.CommError as e:
            print(f"Error logging to Weights & Biases: {e}")

# WebSocket endpoint for generating summaries based on patient data

@app.websocket("/ws_generate_summary")
async def websocket_generate_summary(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print('======================data', data)
            if "/" in data:
                patient_id, category = data.split("/", 1)
            else:
                patient_id, category = data, None
            if category:
                category  = 'patient_info' if category == 'personal_details' else category
                # patient_category_data = fetch_patient_category_data(patient_id, category)
                patient_category_data = query_elasticsearch(patient_id, category)
                print(patient_category_data)
                if not patient_category_data.get(category, ''):
                    await websocket.send_text(f"No data found for category: {category}")
                    continue
                
                # prompt = prepare_category_prompt(patient_category_data, category)
                prompt = Augment(patient_category_data, category)
            else:
                # patient_data = fetch_patient_data(patient_id)
                patient_data = recent_info(patient_id)
                if not patient_data:
                    await websocket.send_text("Patient data not exist")
                    continue
                
                # prompt = prepare_prompt(patient_data)
                prompt = Augment(patient_data, 'recent_health_info')

            async for chunk in generate_summary(prompt):
                await websocket.send_text(chunk)
    except WebSocketDisconnect:
        print("Client disconnected")

# Endpoint to search for patients in Elasticsearch

@app.get("/search")
async def search_patients(q: str = Query(..., min_length=1), size: int = 10):
    return patient_meta(q, size)
