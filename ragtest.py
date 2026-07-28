import chromadb
from google import genai

# 1. Initialize the Gemini Client
client = genai.Client()

# 2. Initialize a local, in-memory Vector Database
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="french_tutor_db")

# Step 1: The Data (Chunk)
grammar_rule = "Le passé composé s'utilise pour exprimer une action spécifique et achevée dans le passé."

# Step 2: The Embedding (Converting text to numbers)
print("--- GENERATING EMBEDDING ---")
embed_response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=grammar_rule
)
# Extract the list of floats
vector = embed_response.embeddings[0].values

print(f"The model turned the sentence into a vector of {len(vector)} numbers.")
print(f"Here are the first 5 coordinates: {vector[:5]}")
print("...\n")

# Step 3: Storing in the Vector Database
print("--- SAVING TO DATABASE ---")
collection.add(
    ids=["rule_1"],            # Every chunk needs a unique ID
    embeddings=[vector],       # The math coordinates
    documents=[grammar_rule],  # The actual text
    metadatas=[{"topic": "grammar", "level": "A2"}]
)
print("Saved successfully!\n")

# Step 4: The Search (Retrieval)
user_question = "Comment je parle d'une action du passé ?"
print(f"--- SEARCHING DATABASE ---")
print(f"User asked: '{user_question}'")

# We must convert the user's question into numbers using the exact same model
question_embed_response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=user_question
)
question_vector = question_embed_response.embeddings[0].values

# Ask ChromaDB to find the 1 closest match in mathematical space
results = collection.query(
    query_embeddings=[question_vector],
    n_results=1
)

print("\n--- RAG RETRIEVAL RESULT ---")
print(f"Retrieved Document: {results['documents'][0][0]}")
print(f"Mathematical Distance: {results['distances'][0][0]} (Lower is closer!)")