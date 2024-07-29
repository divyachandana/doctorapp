# DoctorApp Installation Guide

Follow these steps to set up and run the DoctorApp. Ensure you have the necessary dependencies installed and configured.

## Prerequisites

### 1. Ensure Ollama ROCm is running

Run the following Docker command to start Ollama ROCm:

    docker run -d --device /dev/kfd --device /dev/dri -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama:rocm

### 2. Pull necessary models

Pull the required models into the Ollama container:

    docker exec -it ollama ollama pull llama3.1:70b-instruct-q4_0
    docker exec -it ollama ollama pull llama3.1

### 3. Verify Ollama is running

Check if Ollama is running by visiting [http://localhost:11434/](http://localhost:11434/).

### 4. Ensure Elasticsearch is running

Set the Elasticsearch password:

    export ELASTIC_PASSWORD="elastic"

Create a Docker network for Elasticsearch:

    docker network create elastic-net

Run the Elasticsearch container:

    docker run -d --name elasticsearch --network elastic-net \
      -p 127.0.0.1:9200:9200 \
      -e ELASTIC_PASSWORD=$ELASTIC_PASSWORD \
      -e "discovery.type=single-node" \
      -e "xpack.security.http.ssl.enabled=false" \
      -e "xpack.license.self_generated.type=trial" \
      -e "ES_JAVA_OPTS=-Xms8g -Xmx8g" \
      docker.elastic.co/elasticsearch/elasticsearch:8.14.3

Verify Elasticsearch is running by visiting [http://localhost:9200/](http://localhost:9200/). When prompted, enter `elastic` as both the username and password.

### 5. Create a Weights & Biases account

Create an account on [Weights & Biases](https://wandb.ai) to monitor metrics.

## Installation Steps

### 1. Set up a Python virtual environment

Create and activate a virtual environment:

    python3 -m venv venv
    source venv/bin/activate

### 2. Install required Python packages

Install the dependencies listed in `requirements.txt`:

    pip3 install -r requirements.txt

### 3. Log in to Weights & Biases

Log in to Weights & Biases to start tracking metrics:

    wandb login

### 4. Export Elasticsearch password

Ensure the Elasticsearch password is set:

    export ELASTIC_PASSWORD="elastic"

### 5. Run the FastAPI application

Start the FastAPI application:

    uvicorn app:app --reload

## Additional Resources

For a step-by-step video tutorial, check out this [installation guide](https://youtu.be/lIKbvflIuo0).

---

By following these steps, you should have the DoctorApp up and running. If you encounter any issues, refer to the provided video tutorial or check the documentation for troubleshooting tips.
