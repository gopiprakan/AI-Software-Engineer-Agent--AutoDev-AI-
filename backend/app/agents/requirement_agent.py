import asyncio
from app.agents.base_agent import BaseAgent
from app.agents.templates import get_dynamic_project

class RequirementAgent(BaseAgent):
    def __init__(self):
        super().__init__("Requirement Analyzer", "Business Analyst")

    async def execute(self, state: dict) -> dict:
        self.log("Analyzing user requirements...")
        prompt = state.get("user_prompt", "")
        
        # Check LLM output
        system_prompt = (
            "You are an expert Requirement Analyzer Agent. Your task is to analyze the user's software project proposal "
            "and create a clear requirements document in Markdown format. Outline 1. Project Objectives, 2. Key Modules, "
            "and 3. Detailed Features."
        )
        
        llm_output = await self.call_llm(state, system_prompt, prompt)
        
        if llm_output:
            self.log("LLM successfully generated requirements.")
            state["requirements"] = llm_output
        else:
            self.log("Generating requirements using simulation templates...")
            await asyncio.sleep(1.5)  # Simulate typing/reasoning delay
            proj = get_dynamic_project(prompt)
            state["requirements"] = proj["requirements"]
            
        # Add index file to generated files
        state["files"]["requirements.md"] = state["requirements"]
        self.log("Requirements document generated and added as 'requirements.md'.")
        return state
