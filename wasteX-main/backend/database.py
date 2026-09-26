import os
from typing import Any, Dict, List, Optional
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")


class InMemoryCollection:
    """Fallback in-memory collection when MongoDB is not running."""
    def __init__(self, name: str):
        self.name = name
        self.docs: Dict[str, Dict[str, Any]] = {}

    def insert_one(self, doc: Dict[str, Any]):
        doc_copy = dict(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = ObjectId()
        elif isinstance(doc_copy["_id"], str):
            try:
                doc_copy["_id"] = ObjectId(doc_copy["_id"])
            except Exception:
                pass
        self.docs[str(doc_copy["_id"])] = doc_copy

        class InsertResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id

        return InsertResult(doc_copy["_id"])

    def find_one(self, filter_query: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not filter_query:
            return next(iter(self.docs.values()), None)

        for doc in self.docs.values():
            match = True
            for k, v in filter_query.items():
                if k == "_id":
                    if str(doc.get("_id")) != str(v):
                        match = False
                        break
                elif doc.get(k) != v:
                    match = False
                    break
            if match:
                return dict(doc)
        return None

    def find(self, filter_query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not filter_query:
            return [dict(d) for d in self.docs.values()]

        results = []
        for doc in self.docs.values():
            match = True
            for k, v in filter_query.items():
                if k == "role" and isinstance(v, dict) and "$in" in v:
                    if doc.get(k) not in v["$in"]:
                        match = False
                        break
                elif k == "_id":
                    if str(doc.get("_id")) != str(v):
                        match = False
                        break
                elif doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(dict(doc))
        return results

    def update_one(self, filter_query: Dict[str, Any], update_data: Dict[str, Any]):
        doc = self.find_one(filter_query)
        if doc and "$set" in update_data:
            doc_id = str(doc["_id"])
            self.docs[doc_id].update(update_data["$set"])


class SafeDatabaseProxy:
    """
    Database proxy that attempts real MongoDB operations, falling back gracefully
    to in-memory storage if MongoDB is unavailable in the environment.
    """
    def __init__(self):
        self._mongo_client = None
        self._real_db = None
        self._use_fallback = False
        self._in_memory_collections: Dict[str, InMemoryCollection] = {}

        try:
            from pymongo import MongoClient
            self._mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=800)
            # Quick ping check
            self._mongo_client.admin.command('ping')
            self._real_db = self._mongo_client.waste_x
            print("[Database] Connected to MongoDB at", MONGO_URL)
        except Exception as e:
            print(f"[Database Warning] MongoDB not available ({e}). Using in-memory database fallback.")
            self._use_fallback = True

    def __getattr__(self, name: str):
        if not self._use_fallback and self._real_db is not None:
            try:
                # Test real db attribute access
                return getattr(self._real_db, name)
            except Exception:
                pass
        
        if name not in self._in_memory_collections:
            self._in_memory_collections[name] = InMemoryCollection(name)
        return self._in_memory_collections[name]


database = SafeDatabaseProxy()
