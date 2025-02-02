import logging
from typing import Dict, Any, List
from chromadb import Client, Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_directory: str):
        """Initialize the vector store."""
        try:
            # Initialize ChromaDB client
            self.client = Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))
            
            # Use sentence transformers for embeddings
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction()
            
            # Create collections for different object types
            self.collections = {
                "table": self.client.get_or_create_collection(
                    name="tables",
                    embedding_function=self.embedding_function
                ),
                "view": self.client.get_or_create_collection(
                    name="views",
                    embedding_function=self.embedding_function
                ),
                "procedure": self.client.get_or_create_collection(
                    name="procedures",
                    embedding_function=self.embedding_function
                ),
                "function": self.client.get_or_create_collection(
                    name="functions",
                    embedding_function=self.embedding_function
                )
            }
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the vector store."""
        try:
            return {
                "table": self.collections["table"].count(),
                "view": self.collections["view"].count(),
                "procedure": self.collections["procedure"].count(),
                "function": self.collections["function"].count()
            }
        except Exception as e:
            logger.error(f"Failed to get vector store statistics: {str(e)}")
            return {
                "table": 0,
                "view": 0,
                "procedure": 0,
                "function": 0
            }

    def add_documentation(self, schema: str, name: str, obj_type: str, content: str, metadata: Dict[str, Any]) -> None:
        """Add documentation to the vector store."""
        try:
            collection = self.collections[obj_type]
            doc_id = f"{schema}.{name}"
            
            collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{
                    "schema": schema,
                    "name": name,
                    "type": obj_type,
                    **metadata
                }]
            )
        except Exception as e:
            logger.error(f"Failed to add documentation: {str(e)}")
            raise

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search documentation using natural language."""
        try:
            results = []
            
            # Search each collection
            for obj_type, collection in self.collections.items():
                if collection.count() > 0:  # Only search non-empty collections
                    search_results = collection.query(
                        query_texts=[query],
                        n_results=n_results
                    )
                    
                    # Format results
                    for i in range(len(search_results["ids"][0])):
                        results.append({
                            "id": search_results["ids"][0][i],
                            "content": search_results["documents"][0][i],
                            "metadata": search_results["metadatas"][0][i],
                            "distance": search_results["distances"][0][i]
                        })
            
            # Sort by distance (lower is better)
            results.sort(key=lambda x: x["distance"])
            
            return results[:n_results]
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    def clear(self) -> None:
        """Clear all data from the vector store and reset internal state."""
        logger.info("Starting vector store clear operation")
        cleanup_required = False
        
        try:
            # Mark that we need cleanup in case of failure
            cleanup_required = True
            
            # Clear all collections first
            self.clear_collections()
            
            # Reset the client's internal state
            self.client.reset()
            
            # Reset was successful, no cleanup needed
            cleanup_required = False
            
            logger.info("Vector store successfully cleared")
            
        except Exception as e:
            error_msg = f"Failed to clear vector store: {str(e)}"
            logger.error(error_msg)
            
            if cleanup_required:
                try:
                    logger.info("Attempting cleanup after failed clear operation")
                    # Recreate collections in case they were partially deleted
                    for obj_type in ["table", "view", "procedure", "function"]:
                        self.collections[obj_type] = self.client.get_or_create_collection(
                            name=obj_type + "s",
                            embedding_function=self.embedding_function
                        )
                    logger.info("Cleanup completed successfully")
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {str(cleanup_error)}")
                    raise Exception(f"{error_msg}. Additionally, cleanup failed: {str(cleanup_error)}")
            
            raise Exception(error_msg)

    def clear_collections(self) -> None:
        """Clear all collections in the vector store."""
        try:
            # Delete and recreate each collection
            for obj_type, collection in self.collections.items():
                name = collection.name
                self.client.delete_collection(name)
                self.collections[obj_type] = self.client.create_collection(
                    name=name,
                    embedding_function=self.embedding_function
                )
        except Exception as e:
            logger.error(f"Failed to clear collections: {str(e)}")
            raise