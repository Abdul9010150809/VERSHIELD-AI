"""
High-Speed Vector RAG Service using Azure AI Search
Provides vector-based retrieval-augmented generation
"""

import json
from typing import Dict, List, Any
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import os
from openai import AzureOpenAI
import hashlib


class VectorRAGService:
    """
    Vector-based RAG using Azure AI Search for high-speed retrieval
    """

    def __init__(self, index_name: str = "verishield-knowledge"):
        self.index_name = index_name

        # Azure AI Search
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")

        if self.search_key:
            credential = AzureKeyCredential(self.search_key)
        else:
            credential = DefaultAzureCredential()

        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=credential
        )

        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=credential
        )

        # Azure OpenAI for embeddings
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2023-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        self.embedding_model = os.getenv(
            "AZURE_OPENAI_EMBEDDING_MODEL",
            "text-embedding-ada-002"
        )

        # Initialize index if it doesn't exist
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Create vector search index if it doesn't exist"""
        try:
            # Check if index exists
            self.index_client.get_index(self.index_name)
        except Exception:
            # Create index
            index = SearchIndex(
                name=self.index_name,
                fields=[
                    SimpleField(
                        name="id",
                        type=SearchFieldDataType.String,
                        key=True
                    ),
                    SearchField(
                        name="content",
                        type=SearchFieldDataType.String,
                        searchable=True,
                        retrievable=True
                    ),
                    SearchField(
                        name="title",
                        type=SearchFieldDataType.String,
                        searchable=True,
                        retrievable=True
                    ),
                    SearchField(
                        name="content_vector",
                        type=SearchFieldDataType.Collection(
                            SearchFieldDataType.Single
                        ),
                        searchable=True,
                        vector_search_dimensions=1536,
                        vector_search_profile_name="my-vector-profile"
                    ),
                    SimpleField(
                        name="metadata",
                        type=SearchFieldDataType.String
                    ),
                    SimpleField(
                        name="source",
                        type=SearchFieldDataType.String
                    ),
                    SimpleField(
                        name="timestamp",
                        type=SearchFieldDataType.DateTimeOffset
                    )
                ],
                vector_search=VectorSearch(
                    algorithms=[
                        HnswAlgorithmConfiguration(name="my-hnsw-config")
                    ],
                    profiles=[
                        {
                            "name": "my-vector-profile",
                            "algorithm_configuration_name": "my-hnsw-config"
                        }
                    ]
                )
            )

            self.index_client.create_index(index)

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return []

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to the vector index

        Args:
            documents: List of dicts with 'content', 'title',
                      'metadata', 'source'
        """
        documents_to_index = []

        for doc in documents:
            content = doc.get("content", "")
            if not content:
                continue

            embedding = self._get_embedding(content)
            if not embedding:
                continue

            doc_id = hashlib.md5(content.encode()).hexdigest()

            documents_to_index.append({
                "id": doc_id,
                "content": content,
                "title": doc.get("title", ""),
                "content_vector": embedding,
                "metadata": json.dumps(doc.get("metadata", {})),
                "source": doc.get("source", ""),
                "timestamp": doc.get("timestamp", "2026-01-05T00:00:00Z")
            })

        if documents_to_index:
            try:
                result = self.search_client.upload_documents(
                    documents_to_index
                )
                return len(result) > 0
            except Exception as e:
                print(f"Document indexing failed: {e}")
                return False

        return False

    def search_similar(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity

        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score

        Returns:
            List of similar documents with scores
        """
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return []

        try:
            results = self.search_client.search(
                search_text=None,
                vector_queries=[{
                    "vector": query_embedding,
                    "k": top_k,
                    "fields": "content_vector"
                }],
                select=["content", "title", "metadata", "source", "timestamp"],
                top=top_k
            )

            similar_docs = []
            for result in results:
                score = result.get("@search.score", 0)
                if score >= min_score:
                    similar_docs.append({
                        "content": result.get("content", ""),
                        "title": result.get("title", ""),
                        "metadata": json.loads(result.get("metadata", "{}")),
                        "source": result.get("source", ""),
                        "timestamp": result.get("timestamp", ""),
                        "score": score
                    })

            return similar_docs

        except Exception as e:
            print(f"Vector search failed: {e}")
            return []

    def rag_query(self, query: str, context_window: int = 3) -> Dict[str, Any]:
        """
        Perform RAG query: retrieve relevant docs and generate response

        Args:
            query: User query
            context_window: Number of top documents to include in context

        Returns:
            Generated response with sources
        """
        # Retrieve relevant documents
        relevant_docs = self.search_similar(query, top_k=context_window)

        if not relevant_docs:
            return {
                "response": (
                    "I don't have enough information to "
                    "answer this question."
                ),
                "sources": [],
                "confidence": 0.0
            }

        # Build context from retrieved documents
        context_parts = []
        sources = []

        for doc in relevant_docs:
            context_parts.append(f"Content: {doc['content']}")
            if doc['title']:
                context_parts.append(f"Title: {doc['title']}")
            sources.append({
                "title": doc['title'],
                "source": doc['source'],
                "score": doc['score']
            })

        context = "\n\n".join(context_parts)

        # Generate response using Azure OpenAI
        try:
            system_prompt = (
                "You are a helpful AI assistant. Use the provided "
                "context to answer the user's question accurately.\n"
                "If the context doesn't contain enough information, "
                "say so. Be concise but comprehensive."
            )

            response = self.openai_client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_CHAT_MODEL", "gpt-4"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Context:\n{context}\n\n"
                            f"Question: {query}"
                        )
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )

            generated_response = response.choices[0].message.content

            return {
                "response": generated_response,
                "sources": sources,
                "confidence": (
                    sum(doc['score'] for doc in relevant_docs) /
                    len(relevant_docs)
                ),
                "context_used": len(relevant_docs)
            }

        except Exception as e:
            print(f"RAG generation failed: {e}")
            return {
                "response": (
                    "Sorry, I encountered an error "
                    "generating the response."
                ),
                "sources": sources,
                "confidence": 0.0,
                "error": str(e)
            }

    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from index"""
        try:
            documents_to_delete = [{"id": doc_id} for doc_id in document_ids]
            result = self.search_client.delete_documents(documents_to_delete)
            return len(result) > 0
        except Exception as e:
            print(f"Document deletion failed: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            # Simplified stats - Azure Search doesn't provide direct count
            results = self.search_client.search(
                search_text="*",
                top=1000,
                include_total_count=True
            )
            total_count = (
                results.get_count()
                if hasattr(results, 'get_count')
                else 0
            )

            return {
                "index_name": self.index_name,
                "document_count": total_count,
                "vector_dimensions": 1536,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    rag_service = VectorRAGService()

    # Add sample documents
    sample_docs = [
        {
            "content": (
                "VeriShield AI provides real-time deepfake "
                "detection for financial transactions."
            ),
            "title": "VeriShield Overview",
            "source": "documentation",
            "metadata": {"category": "product"}
        },
        {
            "content": (
                "PII redaction automatically masks sensitive "
                "information like SSN, credit cards, and emails."
            ),
            "title": "PII Redaction Feature",
            "source": "features",
            "metadata": {"category": "security"}
        }
    ]

    rag_service.add_documents(sample_docs)

    # Test RAG query
    result = rag_service.rag_query("What is VeriShield AI?")
    print(f"Response: {result['response']}")
    print(f"Sources: {len(result['sources'])}")
    print(f"Confidence: {result['confidence']:.3f}")
