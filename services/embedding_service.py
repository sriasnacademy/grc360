from groq import Groq
from config.servicekeys import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def generate_embedding(text: str) -> list:
    response = client.embeddings.create(
        model="llama-3.3-70b-versatile",
        input=text
    )
    return response.data[0].embedding
