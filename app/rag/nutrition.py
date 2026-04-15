from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.tools.retriever import create_retriever_tool

from app.config import settings

embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")


def create_nutrition_tool():
    store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=settings.qdrant_url,
        collection_name="nutrition_db",
    )

    return create_retriever_tool(
        store.as_retriever(search_kwargs={"k": 3}),
        name="lookup_nutrition",
        description=(
            "Look up nutritional information for a food item. "
            "Returns calories, protein, carbs, and fat per serving. "
            "Use this before logging a meal to estimate nutrition values."
        ),
    )
