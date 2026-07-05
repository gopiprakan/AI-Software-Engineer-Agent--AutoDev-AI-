import asyncio
from agents.base_agent import BaseAgent
from agents.templates import get_dynamic_project

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Project Planner", "Software Architect")

    async def execute(self, state: dict) -> dict:
        self.log("Planning folder structure and API endpoints...")
        prompt = state.get("user_prompt", "")
        reqs = state.get("requirements", "")
        
        system_prompt = (
            "You are a Project Planner Agent. Based on the requirements document below, define: "
            "1. The project directory layout (in code block tree format).\n"
            "2. A list of main API endpoints (HTTP method, route, details, auth required).\n\n"
            f"Requirements:\n{reqs}"
        )
        
        llm_output = await self.call_llm(state, system_prompt, f"Plan the project structure for: {prompt}")
        
        if llm_output:
            self.log("LLM successfully generated architectural plan.")
            state["plan"] = llm_output
        else:
            self.log("Generating plan using simulation templates...")
            await asyncio.sleep(1.5)
            proj = get_dynamic_project(prompt)
            state["plan"] = proj["plan"]
            
        state["files"]["project_plan.md"] = state["plan"]
        self.log("Project plan and API blueprints saved as 'project_plan.md'.")
        return state
