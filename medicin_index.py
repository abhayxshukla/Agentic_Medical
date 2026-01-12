# import os
# from llama_index.vector_stores.pinecone import PineconeVectorStore
# from pinecone import Pinecone, ServerlessSpec
# from llama_index.embeddings import huggingface
# from llama_index.readers.file import PandasCSVReader
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.core import Settings
# from llama_index.core.chat_engine import SimpleChatEngine, ContextChatEngine
# from llama_index.core.memory import Memory
# from llama_index.core import StorageContext, load_index_from_storage
# from llama_index.core import VectorStoreIndex
# from llama_index.core.prompts import PromptTemplate
# from llama_index.core import StorageContext
# from dotenv import load_dotenv
# load_dotenv()  



# embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
# print("model loaded")

# os.environ["PINECONE_API_KEY"] = "pcsk_5c7qAe_UwH71ccoBtoCz51iiaf8iLuY6mUNKshjk4WUBmGCa26wzN7WqXBzZExd2i8WgSW"
# api_key = os.environ["PINECONE_API_KEY"]

# # Create Pinecone Vector Store
# pc = Pinecone(api_key=api_key)

# # pc.create_index(
# #     name="quickstart",
# #     dimension=1024,
# #     metric="dotproduct",
# #     spec=ServerlessSpec(cloud="aws", region="us-east-1"),
# # )

# pinecone_index = pc.Index(name="1mg",host="https://1mg-p78la0q.svc.aped-4627-b74a.pinecone.io")

# reader=PandasCSVReader(concat_rows=False
# )
# documents=reader.load_data("medicin_vc.csv")

# print("documents loaded")

# vector_store = PineconeVectorStore(
#     pinecone_index=pinecone_index,
# )
# storage_context = StorageContext.from_defaults(vector_store=vector_store)
# index = VectorStoreIndex.from_documents(
#     documents, storage_context=storage_context,show_progress=True, embed_model=embed_model
# )

# print("Index created")

# query_engine = index.as_query_engine()
# response = query_engine.query("What did the author do growing up?")
