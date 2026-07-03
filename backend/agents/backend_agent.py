import asyncio
import json
import re
from agents.base_agent import BaseAgent
from agents.templates import get_dynamic_project

class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__("Backend Generator", "Senior Backend Developer")

    async def execute(self, state: dict) -> dict:
        self.log("Generating FastAPI backend codebase files...")
        prompt = state.get("user_prompt", "")
        db_schema = state.get("database", "")
        
        system_prompt = (
            "You are a Backend Generator Agent. Your task is to output the backend Python files "
            "for a FastAPI application. The files should match the database schema and include routes, schemas, and main app.\n"
            "Respond ONLY with a JSON object where the keys are file paths (e.g. 'backend/app/main.py') "
            "and values are the code contents of those files. Do not output anything outside the JSON code block.\n\n"
            f"Schema:\n{db_schema}"
        )
        
        llm_output = await self.call_llm(state, system_prompt, f"Generate backend files for: {prompt}")
        
        backend_files = {}
        if llm_output:
            # Parse JSON block from LLM
            try:
                # Find JSON block
                json_match = re.search(r"({.*})", llm_output, re.DOTALL)
                if json_match:
                    backend_files = json.loads(json_match.group(1))
                    self.log("LLM successfully generated backend codebase.")
            except Exception as e:
                self.log(f"Failed to parse LLM JSON: {e}. Falling back to simulation.")
        
        if not backend_files:
            self.log("Generating backend files using simulation templates...")
            await asyncio.sleep(2.0)
            proj = get_dynamic_project(prompt)
            backend_files = proj["backend"]

        # Insert files into workspace state
        for path, code in backend_files.items():
            state["files"][path] = code
            self.log(f"Generated file: '{path}' ({len(code)} bytes)")
            
        state["backend_code"] = backend_files
        return state
