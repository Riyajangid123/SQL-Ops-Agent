from langchain_groq import ChatGroq

class LLM:
    def llm(self):
        model = ChatGroq(model="llama-3.3-70b-versatile")

        try:
            from main import mcp_context
            mcp_tools = mcp_context.get("tools", [])
            
            if mcp_tools:
                print(f"🔌 [LLM] Successfully bound {len(mcp_tools)} MCP tools to Llama-3.3.")
                return model.bind_tools(mcp_tools)
        except Exception as e:
            print(f"⚠️ [LLM] Fallback triggered (could not bind MCP tools): {str(e)}")
            
        return model