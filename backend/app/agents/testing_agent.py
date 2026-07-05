import asyncio
from agents.base_agent import BaseAgent
from agents.templates import get_dynamic_project

class TestingAgent(BaseAgent):
    def __init__(self):
        super().__init__("Test Generator", "Software Development Engineer in Test (SDET)")

    async def execute(self, state: dict) -> dict:
        self.log("Writing automated unit tests...")
        prompt = state.get("user_prompt", "")
        backend_code = state.get("backend_code", {})
        
        # Sample code for testing
        main_code = backend_code.get("backend/app/main.py", "")
        
        system_prompt = (
            "You are a Test Generator Agent. Write standard pytest unit tests for a FastAPI backend application "
            "based on the provided entry point code. Output only the code contents inside python markdown format."
        )
        
        llm_output = await self.call_llm(state, system_prompt, f"Write pytest scripts for backend code:\n{main_code[:1000]}")
        
        if llm_output:
            self.log("LLM successfully generated test cases.")
            state["tests"] = llm_output
        else:
            self.log("Generating unit tests in simulated mode...")
            await asyncio.sleep(1.5)
            proj = get_dynamic_project(prompt)
            state["tests"] = proj["tests"]
            
        state["files"]["backend/tests/test_api.py"] = state["tests"]
        self.log("Test suite generated and saved as 'backend/tests/test_api.py'.")
        return state
