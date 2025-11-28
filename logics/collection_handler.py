import chromadb
import langchain
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('.env')


# ---------------------------
# Initialize Persistent Chroma DB
# ---------------------------
# Data will be stored in ./{collection_path}

#client = chromadb.PersistentClient(path=collection_path)
client = chromadb.EphemeralClient()
collection = client.get_or_create_collection(name="issues_collection")

# ---------------------------
# Embeddings & LLM
# ---------------------------
emb = OpenAIEmbeddings(model="text-embedding-3-small")
llm = OpenAI()


def initCollection(df_InitIssues):
    if len(collection.get()["ids"]) == 0:
        addMultipleIssues(df_InitIssues)
    

def viewAllIssues():
    data = collection.get()
    list_of_pairs = []
    if data["ids"]:
       for doc, meta in zip(data["documents"], data["metadatas"]):
            list_of_pairs.append(meta)
    return list_of_pairs

def addIssue(issue,resolution):
    doc_text = f"Issue: {issue}\nResolution: {resolution}"
    vector = emb.embed_query(doc_text)
    doc_id = f"issue_{hash(issue)}"
    collection.add(
        documents=[doc_text],
        metadatas=[{"Issue": issue, "Resolution": resolution}],
        ids=[doc_id],
        embeddings=[vector]
    )

def addMultipleIssues(df_Issues):
    
    def process_row(row):
        issue = str(row['issue'])
        resolution = str(row['resolution'])
        doc_text = f"Issue: {issue}\nResolution: {resolution}"
        vector = emb.embed_query(doc_text)
        doc_id = f"issue_{hash(issue)}"
        return (doc_text, {"Issue": issue, "Resolution": resolution}, doc_id, vector)

    # ThreadPoolExecutor for async embedding generation
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_row, [row for _, row in df_Issues.iterrows()]))

    # Add all entries to persistent Chroma
    for doc_text, metadata, doc_id, vector in results:
        collection.add(
            documents=[doc_text],
            metadatas=[metadata],
            ids=[doc_id],
            embeddings=[vector]
        )

def queryCollection(userInput):
    q_vec = emb.embed_query(userInput)
    results = collection.query(query_embeddings=[q_vec], n_results=5)
    
    if results["documents"]:
        context = "\n\n".join(results["documents"][0])
        prompt = f"""
You are an IT helpdesk specialist for an enterprise IT system
Your job is to recommend actionable solutions based strictly on retrieved past cases.

Follow thse strict rules:
1) Recommend only context-supported solution relevant to the user query.
2) Do not guess or fabricate - only use retrieved facts.
3) List multiple valid solutions as bullets.
4) After each solution, briefly state why it work.

Here are some issue-resolution pairs:

{context}

Answer the user's question using ONLY the information above. Answer in bullet form where possible
If the answer is not found in the data, say "I don't know based on the stored issues but these are the possible resolution from the internet" and propose generic answer

User question:
{userInput}
"""
        response = llm.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        
        answer = response.choices[0].message.content
    return results, answer