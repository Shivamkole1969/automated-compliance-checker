import chromadb

from data import POLICIES

COLLECTION_NAME = "company_policies"


def build_store(policies=POLICIES):
    client = chromadb.Client()
    collection = client.get_or_create_collection(COLLECTION_NAME)
    collection.upsert(
        ids=[p["id"] for p in policies],
        documents=[p["text"] for p in policies],
        metadatas=[{"section": p["section"]} for p in policies],
    )
    return collection


def search(collection, query, top_k=2):
    top_k = min(top_k, collection.count())
    if top_k == 0:
        return []

    result = collection.query(query_texts=[query], n_results=top_k)
    return [
        {"id": policy_id, "text": document, "section": metadata["section"], "distance": distance}
        for policy_id, document, metadata, distance in zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        )
    ]
