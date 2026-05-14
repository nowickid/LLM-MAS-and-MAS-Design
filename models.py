from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_ollama import ChatOllama
from langchain_perplexity import ChatPerplexity
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.callbacks import StreamingStdOutCallbackHandler

load_dotenv()

gemini_3_flash = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }
)

gemini_2_5_flash = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview",
    temperature=0,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }
)
gemini_3_1_flash_lite = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
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

qwen = ChatOllama(
    model="qwen2.5:32b-instruct",  
    base_url="http://localhost:11434",
    temperature=0.1
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
critic_llm =        qwen
creator_llm =       gemini_3_1_flash_lite
optimization_llm =  qwen

# IMPLEMENTATION
architect_llm =     gemini_3_1_flash_lite
menager_llm =       gemini_3_1_flash_lite
worker_llm =        qwen


# critic_llm =        qwen
# creator_llm =       qwen
# optimization_llm =  qwen

# # IMPLEMENTATION
# architect_llm =     qwen
# menager_llm =       qwen
# worker_llm =        qwen