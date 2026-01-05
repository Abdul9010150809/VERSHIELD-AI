"""
High-Speed Vector RAG using Azure AI Search
Knowledge retrieval with hybrid search capabilities
"""
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch
)
from azure.core.credentials import AzureKeyCredential
from openai import AsyncOpenAI
import json

class VectorRAG:
    """
    High-performance RAG using Azure AI Search with vector and hybrid search
    """
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX", "verishield-knowledge")
        
        api_key = os.getenv("OPENAI_API_KEY")
        # Only initialize OpenAI client if API key is provided and not a placeholder
        if api_key and not api_key.startswith("sk-proj-test"):
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            self.openai_client = None
        
        if self.endpoint and self.key:
            self.search_client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=AzureKeyCredential(self.key)
            )
            self.index_client = SearchIndexClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        else:
            self.search_client = None
            self.index_client = None
            print("Warning: Azure Search credentials not configured")
    
    async def create_index(self):
        """
        Create or update the search index with vector search capabilities
        """
        if not self.index_client:
            return {"success": False, "error": "Index client not configured"}
        
        try:
            # Define vector search configuration
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="vector-profile",
                        algorithm_configuration_name="hnsw-config"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="hnsw-config",
                        parameters={
                            "m": 4,
                            "ef_construction": 400,
                            "ef_search": 500,
                            "metric": "cosine"
                        }
                    )
                ]
            )
            
            # Define semantic search configuration
            semantic_config = SemanticConfiguration(
                name="semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                    keywords_fields=[SemanticField(field_name="category")]
                )
            )
            
            semantic_search = SemanticSearch(
                configurations=[semantic_config]
            )
            
            # Define index fields
            fields = [
                SearchField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True
                ),
                SearchField(
                    name="title",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True
                ),
                SearchField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True
                ),
                SearchField(
                    name="category",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                    facetable=True
                ),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="vector-profile"
                ),
                SearchField(
                    name="metadata",
                    type=SearchFieldDataType.String
                ),
                SearchField(
                    name="timestamp",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True
                )
            ]
            
            # Create index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search
            )
            
            async with self.index_client:
                result = await self.index_client.create_or_update_index(index)
                
            return {
                "success": True,
                "index_name": result.name,
                "field_count": len(result.fields)
            }
            
        except Exception as e:
            print(f"Index creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        """
        if not self.openai_client:
            # Return empty list if OpenAI client is not available
            return []
        
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return []
    
    async def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index a single document with vector embedding
        """
        if not self.search_client:
            return {"success": False, "error": "Search client not configured"}
        
        try:
            # Generate embedding
            embedding = await self.get_embedding(content)
            
            if not embedding:
                return {"success": False, "error": "Failed to generate embedding"}
            
            # Prepare document
            document = {
                "id": doc_id,
                "title": title,
                "content": content,
                "category": category,
                "embedding": embedding,
                "metadata": json.dumps(metadata or {}),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Upload to index
            async with self.search_client:
                result = await self.search_client.upload_documents(documents=[document])
                
            return {
                "success": result[0].succeeded,
                "doc_id": doc_id,
                "status": result[0].status_code
            }
            
        except Exception as e:
            print(f"Document indexing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def batch_index_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch index multiple documents
        """
        if not self.search_client:
            return {"success": False, "error": "Search client not configured"}
        
        try:
            # Generate embeddings for all documents
            tasks = [self.get_embedding(doc["content"]) for doc in documents]
            embeddings = await asyncio.gather(*tasks)
            
            # Prepare documents
            indexed_docs = []
            for i, doc in enumerate(documents):
                if embeddings[i]:
                    indexed_docs.append({
                        "id": doc["id"],
                        "title": doc["title"],
                        "content": doc["content"],
                        "category": doc.get("category", "general"),
                        "embedding": embeddings[i],
                        "metadata": json.dumps(doc.get("metadata", {})),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Upload batch
            async with self.search_client:
                results = await self.search_client.upload_documents(documents=indexed_docs)
            
            success_count = sum(1 for r in results if r.succeeded)
            
            return {
                "success": True,
                "total_documents": len(documents),
                "successful": success_count,
                "failed": len(documents) - success_count
            }
            
        except Exception as e:
            print(f"Batch indexing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def vector_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search
        """
        if not self.search_client:
            return []
        
        try:
            # Generate query embedding
            query_embedding = await self.get_embedding(query)
            
            if not query_embedding:
                return []
            
            # Perform vector search
            async with self.search_client:
                results = await self.search_client.search(
                    search_text=None,
                    vector_queries=[{
                        "kind": "vector",
                        "vector": query_embedding,
                        "fields": "embedding",
                        "k": top_k
                    }],
                    filter=filters,
                    select=["id", "title", "content", "category", "metadata"]
                )
                
                documents = []
                async for result in results:
                    documents.append({
                        "id": result["id"],
                        "title": result["title"],
                        "content": result["content"],
                        "category": result["category"],
                        "metadata": json.loads(result.get("metadata", "{}")),
                        "score": result["@search.score"]
                    })
                
                return documents
            
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        use_semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + keyword + semantic)
        """
        if not self.search_client:
            return []
        
        try:
            # Generate query embedding
            query_embedding = await self.get_embedding(query)
            
            search_params = {
                "search_text": query,
                "top": top_k,
                "select": ["id", "title", "content", "category", "metadata"]
            }
            
            if query_embedding:
                search_params["vector_queries"] = [{
                    "kind": "vector",
                    "vector": query_embedding,
                    "fields": "embedding",
                    "k": top_k
                }]
            
            if use_semantic:
                search_params["query_type"] = "semantic"
                search_params["semantic_configuration_name"] = "semantic-config"
            
            async with self.search_client:
                results = await self.search_client.search(**search_params)
                
                documents = []
                async for result in results:
                    documents.append({
                        "id": result["id"],
                        "title": result["title"],
                        "content": result["content"],
                        "category": result["category"],
                        "metadata": json.loads(result.get("metadata", "{}")),
                        "score": result["@search.score"],
                        "reranker_score": result.get("@search.reranker_score")
                    })
                
                return documents
            
        except Exception as e:
            print(f"Hybrid search error: {e}")
            return []
    
    async def retrieve_and_generate(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        RAG: Retrieve relevant documents and generate response
        """
        # Retrieve relevant documents
        documents = await self.hybrid_search(query, top_k=top_k)
        
        if not documents:
            return {
                "answer": "I don't have enough information to answer this question.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Prepare context from retrieved documents
        context = "\n\n".join([
            f"Source: {doc['title']}\n{doc['content']}"
            for doc in documents
        ])
        
        # Generate response using context
        system_message = system_prompt or """You are a helpful AI assistant. 
        Answer the question based on the provided context. 
        If the context doesn't contain relevant information, say so clearly."""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                temperature=0.7
            )
            
            return {
                "answer": response.choices[0].message.content,
                "sources": documents,
                "confidence": min(documents[0]["score"] if documents else 0, 1.0),
                "model": response.model,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            print(f"Generation error: {e}")
            return {
                "answer": "Error generating response",
                "sources": documents,
                "error": str(e)
            }
    
    async def close(self):
        """Close connections"""
        if self.search_client:
            await self.search_client.close()
        if self.index_client:
            await self.index_client.close()
