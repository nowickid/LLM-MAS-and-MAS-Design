from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_ollama import ChatOllama
from langchain_perplexity import ChatPerplexity
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()
gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }
)


ollama = ChatOllama(
    model="llama3.3:70b",  
    base_url="http://localhost:11434",
    temperature=0
)

gwen = ChatOllama(
    model="qwen2.5:72b",  
    base_url="http://localhost:11434",
    temperature=0
)
perplexity = ChatPerplexity(
    temperature=0, 
    model="sonar"
)
groq = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.0
)

# GAIA
critic_llm = gwen
creator_llm = gemini
optimization_llm = gemini
# IMPLEMENTATION
architect_llm = gwen
menager_llm = gwen
worker_llm = gwen