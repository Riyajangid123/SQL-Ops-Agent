from langchain_groq import ChatGroq

class LLM:
    def llm(self):
        model=ChatGroq(model="llama-3.3-70b-versatile")

        return model