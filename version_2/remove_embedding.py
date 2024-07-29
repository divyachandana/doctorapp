import shutil
import os

# Define the path to the vectorstore directory
vectorstore_path = "./vectorstore"

# Check if the vectorstore directory exists
if os.path.exists(vectorstore_path):
    # Remove the existing vectorstore directory
    shutil.rmtree(vectorstore_path)

# Recreate the vectorstore directory
os.makedirs(vectorstore_path)