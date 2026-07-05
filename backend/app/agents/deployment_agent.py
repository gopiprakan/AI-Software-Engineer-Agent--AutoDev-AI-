import asyncio
from app.agents.base_agent import BaseAgent
from app.agents.templates import get_dynamic_project

class DeploymentAgent(BaseAgent):
    def __init__(self):
        super().__init__("Deployment Configurator", "DevOps Engineer")

    async def execute(self, state: dict) -> dict:
        self.log("Generating deployment configurations and guides...")
        prompt = state.get("user_prompt", "")
        
        system_prompt = (
            "You are an expert DevOps and Deployment Configurator Agent. Your task is to analyze the user's software project proposal "
            "and generate two things:\n"
            "1. A Dockerfile setup appropriate for this project.\n"
            "2. A deployment guide in Markdown format (outline: 1. Architecture Overview, 2. Local Run via Docker, 3. Deployment Instructions, 4. Environment Setup).\n"
            "Combine both into a single text output, separated by '---DOCKERFILE_DEPLOY_SEPARATOR---'. Put the Dockerfile content first, then the separator, then the deployment guide Markdown."
        )
        
        llm_output = await self.call_llm(state, system_prompt, prompt)
        
        dockerfile_content = ""
        deploy_guide_content = ""
        
        if llm_output and "---DOCKERFILE_DEPLOY_SEPARATOR---" in llm_output:
            self.log("LLM successfully generated deployment setup.")
            parts = llm_output.split("---DOCKERFILE_DEPLOY_SEPARATOR---", 1)
            dockerfile_content = parts[0].strip()
            deploy_guide_content = parts[1].strip()
        else:
            self.log("Generating deployment files using simulation templates...")
            await asyncio.sleep(1.5)  # Simulate typing/reasoning delay
            proj = get_dynamic_project(prompt)
            # Fetch from templates
            dockerfile_content = proj.get("dockerfile", "# Default Dockerfile\nFROM node:18-alpine\nWORKDIR /app\nCOPY . .\nRUN npm install\nCMD [\"npm\", \"run\", \"dev\"]")
            deploy_guide_content = proj.get("deploy_guide", "# Deployment Guide\n\n## 1. Architecture Overview\nThis project is structured as a fullstack application.\n\n## 2. Local Run\nRun `docker build -t app .` and then `docker run -p 3000:3000 app`.")
            
        state["files"]["Dockerfile"] = dockerfile_content
        state["files"]["deploy.md"] = deploy_guide_content
        self.log("Deployment configuration ('Dockerfile' and 'deploy.md') generated successfully.")
        return state
