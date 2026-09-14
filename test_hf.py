from langchain_huggingface import HuggingFaceEmbeddings

print("Attempting to load BAAI/bge-small-en-v1.5...")
try:
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    print("Successfully loaded model!")
except Exception as e:
    print(f"Error loading model: {e}")
