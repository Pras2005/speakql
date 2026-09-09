# 🗣️ SpeakQL

**Agentic Natural Language to SQL Engine**

SpeakQL is an intelligent pipeline that translates natural language questions into precise, safe SQL queries using a ReAct-style agentic architecture. 

**Note:** Built entirely from scratch *without* LangChain.

### ✨ Core Features
*   **ReAct-Style Agent Pipeline:** The LLM iteratively reasons, selects internal tools, and self-corrects its SQL queries based on database errors.
*   **Dynamic Schema Introspection:** Automatically reads and understands the database schema structure without hardcoding.
*   **Multi-Layer SQL Safety Guard:** Ensures only safe, non-destructive read operations are executed on the database.

### 🏆 Achievements
*   **Runner-Up** - DBMS Competition

### 🛠️ Tech Stack
Python $\cdot$ LLM APIs (Gemini/OpenAI) $\cdot$ PostgreSQL

---
*Created by Prasad Desale.*
