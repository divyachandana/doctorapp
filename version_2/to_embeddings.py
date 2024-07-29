import time
import torch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from model import fetch_all_patient_data, prepare_prompt_all, fetch_all_patient_ids

# Initialize Ollama embeddings and vector store
oembed = OllamaEmbeddings(base_url="http://localhost:11434", model="mxbai-embed-large")
vectorstore = Chroma(embedding_function=oembed, persist_directory="./vectorstore")

if not torch.cuda.is_available():
    print("CUDA is not available. Using CPU.")
else:
    print(f"Using GPU: {torch.cuda.get_device_name(torch.cuda.current_device())}")

def fetch_all_patient_data_sync(patient_id):
    try:
        return fetch_all_patient_data(patient_id)
    except Exception as e:
        print(f"Error fetching data for patient {patient_id}: {e}")
        return None

def precompute_embeddings():
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    
    patient_ids = fetch_all_patient_ids()

    total_time = 0
    count = 0
    
    for idx, patient_id in enumerate(patient_ids, start=1):
        start_time = time.time()
        
        patient_data = fetch_all_patient_data_sync(patient_id)
        
        if patient_data is None:
            continue

        prompt = prepare_prompt_all(patient_data)
        
        # Split the prompt into smaller chunks
        chunks = text_splitter.split_text(prompt)
        
        # Convert each chunk into a document with metadata
        documents = [Document(page_content=chunk, metadata={"patient_id": patient_id}) for chunk in chunks]
        
        # Add documents to vector store
        vectorstore.add_documents(documents)

        end_time = time.time()
        elapsed_time = end_time - start_time
        total_time += elapsed_time
        count += 1
        
        print(f"{idx} Processed patient {patient_id} in {elapsed_time:.2f} seconds")
        if idx % 1000 == 0:
            average_time = total_time / count
            print(f"Average time for the last 1000 patients: {average_time:.2f} seconds per patient")
            total_time = 0
            count = 0


# Run the precomputation process
if __name__ == "__main__":
    try:
        precompute_embeddings()
        print("Precomputed embeddings and stored in the vector database successfully.")
    except Exception as e:
        print(f"An error occurred during the precomputation process: {e}")
