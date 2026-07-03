import asyncio
from agents.base_agent import BaseAgent
from agents.templates import get_dynamic_project

class DatabaseAgent(BaseAgent):
    def __init__(self):
        super().__init__("Database Designer", "Database Administrator")

    async def execute(self, state: dict) -> dict:
        self.log("Designing database tables and DDL queries...")
        prompt = state.get("user_prompt", "")
        plan = state.get("plan", "")
        
        system_prompt = (
            "You are a Database Designer Agent. Based on the project architecture plan, "
            "write SQL DDL statements (CREATE TABLE, relationships, foreign keys, indexes) and seed SQL commands "
            "suitable for PostgreSQL, MySQL, or SQLite.\n\n"
            f"Project Plan:\n{plan}"
        )
        
        llm_output = await self.call_llm(state, system_prompt, f"Design database for: {prompt}")
        
        if llm_output:
            self.log("LLM successfully generated database script.")
            state["database"] = llm_output
        else:
            self.log("Generating database configuration using simulation templates...")
            await asyncio.sleep(1.5)
            proj = get_dynamic_project(prompt)
            state["database"] = proj["database"]
            
        state["files"]["database_schema.sql"] = state["database"]
        self.log("Database schema design completed and saved as 'database_schema.sql'.")
        return state
