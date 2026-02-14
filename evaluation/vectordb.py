import os
import json
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

class VectorDBBuilder:
    """
    Core engine for Layer-3 (The Manual). 
    Handles embedding generation, storage in ChromaDB, and metadata-rich retrieval.
    """
    def __init__(self, persist_directory: str = "./.chromadb", model_name: str = "all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.model = SentenceTransformer(model_name)

    def get_collection(self, name: str):
        return self.client.get_or_create_collection(name=name)

    def query(self, query_text: str, collection_name: str = "sharia_knowledge", k: int = 5) -> Dict:
        """
        Queries the VectorDB and returns results with parsed Knowledge Packages.
        """
        collection = self.get_collection(collection_name)
        embedding = self.model.encode(query_text).tolist()
        
        results = collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        for i in range(len(results['ids'][0])):
            # Chroma stores metadata as flat key-values; we reconstruct the knowledge_package
            raw_meta = results['metadatas'][0][i]
            
            # Reconstruct the Knowledge Package dict from flat metadata
            kp = {
                "canonical_id": raw_meta.get("canonical_id"),
                "source_integrity_score": float(raw_meta.get("source_integrity_score", 0.0)),
                "scholarly_grading": raw_meta.get("scholarly_grading"),
                "tafsir": raw_meta.get("tafsir_snippet"),
                "citation": raw_meta.get("citation")
            }

            formatted_results.append({
                "id": results['ids'][0][i],
                "distance": results['distances'][0][i],
                "document": results['documents'][0][i],
                "metadata": {**raw_meta, "knowledge_package": kp}
            })

        return {"results": formatted_results}

def _extract_scholarly_grading(text: str, source: str) -> Dict[str, Any]:
    """
    Heuristically determines the integrity score based on classical grading.
    """
    text_lower = text.lower()
    grading = "unknown"
    score = 0.5 # Baseline

    if source == "Quran":
        grading = "Mutawatir (Absolute)"
        score = 1.0
    elif any(word in text_lower for word in ["sahih", "authentic", "bukhari", "muslim"]):
        grading = "Sahih"
        score = 0.95
    elif any(word in text_lower for word in ["hasan", "good"]):
        grading = "Hasan"
        score = 0.75
    elif any(word in text_lower for word in ["daif", "weak", "munkar"]):
        grading = "Da'if"
        score = 0.3
    
    return {"grade": grading, "score": score}

def build_sharia_knowledge_packages(corpus_folder: str, persist_directory: str) -> Dict:
    """
    Master ingestion function: Parses Quran SQLite and Hadith JSONs into ChromaDB.
    """
    builder = VectorDBBuilder(persist_directory=persist_directory)
    collection = builder.get_collection("sharia_knowledge")
    
    stats = {"quran_verses": 0, "hadith_entries": 0, "total_indexed": 0}
    
    # 1. Process Quran (SQLite)
    quran_path = os.path.join(corpus_folder, "Quraan.db")
    if os.path.exists(quran_path):
        conn = sqlite3.connect(quran_path)
        # Using Ibn Kathir (IK) table for tafsir as per user workflow
        query = "SELECT a.SURA_num, a.AYA_num, a.Text, t.Tafsir_text FROM Ayahs a JOIN IK t ON a.SURA_num = t.SURA_num AND a.AYA_num = t.AYA_num"
        df = pd.read_sql_query(query, conn)
        
        for _, row in df.iterrows():
            cid = f"Quran {row['SURA_num']}:{row['AYA_num']}"
            grading = _extract_scholarly_grading("", "Quran")
            text = f"Verse: {row['Text']} | Tafsir: {row['Tafsir_text'][:500]}"
            
            collection.add(
                ids=[f"q_{row['SURA_num']}_{row['AYA_num']}"],
                documents=[text],
                metadatas=[{
                    "source_file": "Quraan.db",
                    "canonical_id": cid,
                    "scholarly_grading": grading['grade'],
                    "source_integrity_score": grading['score'],
                    "tafsir_snippet": row['Tafsir_text'][:200],
                    "citation": cid
                }],
                embeddings=[builder.model.encode(text).tolist()]
            )
            stats["quran_verses"] += 1
        conn.close()

    # 2. Process Hadith (JSON)
    for file in os.listdir(corpus_folder):
        if file.endswith(".json") and "knowledge_packages" not in file:
            path = os.path.join(corpus_folder, file)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for i, item in enumerate(data):
                    h_text = item.get("english", {}).get("text", str(item))
                    grading = _extract_scholarly_grading(str(item), "Sunna")
                    cid = f"{file.split('.')[0]} {item.get('id', i)}"
                    
                    collection.add(
                        ids=[f"h_{file}_{i}"],
                        documents=[h_text],
                        metadatas=[{
                            "source_file": file,
                            "canonical_id": cid,
                            "scholarly_grading": grading['grade'],
                            "source_integrity_score": grading['score'],
                            "citation": cid
                        }],
                        embeddings=[builder.model.encode(h_text).tolist()]
                    )
                    stats["hadith_entries"] += 1

    stats["total_indexed"] = stats["quran_verses"] + stats["hadith_entries"]
    return stats

def query_sharia_knowledge(query: str, k: int = 5, persist_directory: str = "./.chromadb"):
    """Convenience wrapper for Phase 3 testing."""
    builder = VectorDBBuilder(persist_directory=persist_directory)
    return builder.query(query, k=k)