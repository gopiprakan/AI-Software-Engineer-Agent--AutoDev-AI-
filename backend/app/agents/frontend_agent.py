import asyncio
import json
import re
from app.agents.base_agent import BaseAgent
from app.agents.templates import get_dynamic_project

class FrontendAgent(BaseAgent):
    def __init__(self):
        super().__init__("Frontend Generator", "Senior Frontend Developer")

    async def execute(self, state: dict) -> dict:
        self.log("Generating React frontend codebase files...")
        prompt = state.get("user_prompt", "")
        backend_code = state.get("backend_code", {})
        
        system_prompt = (
            "You are a Frontend Generator Agent. Your task is to output the frontend React files "
            "for a Vite application. The files should look premium and make calls to the backend APIs.\n"
            "Respond ONLY with a JSON object where the keys are file paths (e.g. 'frontend/src/App.jsx') "
            "and values are the code contents. Do not output anything outside the JSON block.\n\n"
            f"Backend Code context:\n{list(backend_code.keys())}"
        )
        
        llm_output = await self.call_llm(state, system_prompt, f"Generate frontend files for: {prompt}")
        
        frontend_files = {}
        if llm_output:
            try:
                json_match = re.search(r"({.*})", llm_output, re.DOTALL)
                if json_match:
                    frontend_files = json.loads(json_match.group(1))
                    self.log("LLM successfully generated frontend codebase.")
            except Exception as e:
                self.log(f"Failed to parse LLM JSON: {e}. Falling back to simulation.")
                
        if not frontend_files:
            self.log("Generating frontend files using simulation templates...")
            await asyncio.sleep(2.0)
            proj = get_dynamic_project(prompt)
            frontend_files = proj["frontend"]

        # Insert files into workspace state
        for path, code in frontend_files.items():
            state["files"][path] = code
            self.log(f"Generated file: '{path}' ({len(code)} bytes)")
            
        state["frontend_code"] = frontend_files
        return state
