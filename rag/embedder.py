import chromadb
from chromadb.utils import embedding_functions

# ChromaDB client banate hai - ye disk pe data save karega "chroma_db" folder mein
client = chromadb.PersistentClient(path="./chroma_db")

# Default embedding function use kar rahe hai (chhota, free, local model)
embedding_function = embedding_functions.DefaultEmbeddingFunction()

# Ek "collection" banate hai - ye jaise ek table hoti hai database mein
collection = client.get_or_create_collection(
    name="codebase",
    embedding_function=embedding_function
)


def chunk_code(filepath):
    """
    Ye function ek Python file ko padhta hai aur usse
    function/class ke hisab se chhote chunks mein todta hai.
    """
    with open(filepath, "r") as f:
        lines = f.readlines()
    
    chunks = []
    current_chunk = []
    current_name = "module_level"
    
    for line in lines:
        # Agar naya function/class shuru ho raha hai, purana chunk save karo
        if line.startswith("def ") or line.startswith("class "):
            if current_chunk:
                chunks.append({
                    "name": current_name,
                    "code": "".join(current_chunk)
                })
            current_chunk = [line]
            current_name = line.strip().split("(")[0].split(":")[0]
        else:
            current_chunk.append(line)
    
    # Aakhri chunk bhi add karo
    if current_chunk:
        chunks.append({
            "name": current_name,
            "code": "".join(current_chunk)
        })
    
    return chunks


def embed_file(filepath):
    """
    Ye function ek file ko chunks mein todta hai,
    aur har chunk ko ChromaDB mein store karta hai.
    """
    chunks = chunk_code(filepath)
    
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk["code"]],
            metadatas=[{"filepath": filepath, "name": chunk["name"]}],
            ids=[f"{filepath}::{chunk['name']}::{i}"]
        )
    
    print(f"Embedded {len(chunks)} chunks from {filepath}")


def search_similar_code(query, n_results=3):
    """
    Ye function ek query (jaise 'function that adds numbers')
    leta hai aur codebase mein similar chunks dhoondta hai.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results


if __name__ == "__main__":
    # Test: dono sample files ko embed karo
    embed_file("data/sample_code.py")
    embed_file("data/insecure_code.py")
    
    # Test: kuch search karke dekho
    print("\n--- Searching for 'function that manages users' ---")
    results = search_similar_code("function that manages users")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"\nFound in {meta['filepath']} ({meta['name']}):")
        print(doc[:100] + "...")