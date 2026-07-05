import asyncio
from app.agents.base_agent import BaseAgent
from app.agents.templates import get_dynamic_project

class DocumentationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Documentation Generator", "Technical Writer")

    async def execute(self, state: dict) -> dict:
        self.log("Assembling comprehensive documentation manuals...")
        prompt = state.get("user_prompt", "")
        
        system_prompt = (
            "You are a Documentation Agent. Generate a README.md file explaining the project requirements, "
            "architecture structure, API routing endpoints, and detailed local installation steps."
        )
        
        llm_output = await self.call_llm(state, system_prompt, f"Document this project: {prompt}")
        
        docs = {}
        if llm_output:
            self.log("LLM successfully generated README document.")
            docs = {
                "README.md": llm_output,
                "API_DOCS.md": "# API Reference\nRefer to standard endpoints specified in README.md",
                "INSTALL.md": "# Installation Steps\nRefer to instructions in README.md"
            }
        else:
            self.log("Generating documentation suite using simulation templates...")
            await asyncio.sleep(1.5)
            proj = get_dynamic_project(prompt)
            docs = proj["docs"]

        # Save files
        for path, content in docs.items():
            state["files"][path] = content
            self.log(f"Generated documentation file: '{path}'")
            
        state["docs"] = docs
        return state
