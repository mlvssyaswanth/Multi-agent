"""
Deployment Configuration Agent - Generates deployment files and instructions.
"""
from typing import Dict
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class DeploymentAgent:
    """Agent responsible for generating deployment configuration files."""
    
    def __init__(self):
        """Initialize the Deployment Configuration Agent."""
        self.agent = ConversableAgent(
            name="deployment_specialist",
            system_message="""You are a DevOps Engineer specializing in Python project deployment and configuration.

PRIMARY MISSION:
Generate deployment configuration focusing on simplicity and reproducibility.

CORE RESPONSIBILITIES:
1. **Generate requirements.txt**: List all Python dependencies with versions
2. **Generate Project Setup Instructions**: Clear, step-by-step setup guide
3. **GitHub Push Instructions**: How to push the project to GitHub
4. **Hosting Platform Recommendations**: Suggest compatible hosting platforms
5. **Focus on Simplicity and Reproducibility**: Make setup easy and repeatable

MANDATORY OUTPUTS:

1. **requirements.txt**:
   - List all Python dependencies needed
   - Include version numbers where critical
   - Format: package>=version or package==version
   - Be complete and accurate

2. **Project Setup Instructions**:
   - Step-by-step instructions for setting up the project locally
   - Include: Python version, virtual environment setup, dependency installation
   - Make it simple and easy to follow
   - Ensure reproducibility (anyone can follow and get same result)

3. **GitHub Push Instructions**:
   - How to initialize a git repository
   - How to create a .gitignore file (if needed)
   - How to add files and commit
   - How to create a GitHub repository
   - How to push code to GitHub
   - Step-by-step commands

4. **Hosting Platform Recommendations**:
   - Analyze the project type and requirements
   - Suggest compatible hosting platforms (e.g., Heroku, Railway, Render, Vercel, AWS, Google Cloud, etc.)
   - Explain why each platform is suitable
   - Provide brief deployment steps for recommended platforms
   - Consider: web apps, APIs, CLI tools, data processing, etc.

FOCUS PRINCIPLES:
- **Simplicity**: Instructions should be clear and easy to follow
- **Reproducibility**: Anyone following instructions should get the same working setup
- **Completeness**: Include all necessary steps, no assumptions
- **Clarity**: Use simple language and clear formatting

Output Format:
Provide your output as structured text that can be parsed into:
- requirements.txt content
- Setup instructions
- GitHub push instructions
- Hosting platform recommendations""",
            llm_config={
                "config_list": [{
                    "model": Config.MODEL,
                    "api_key": Config.OPENAI_API_KEY,
                    "temperature": Config.TEMPERATURE,
                }],
                "timeout": 120,
            },
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
        )
    
    def generate_deployment_config(self, code: str, requirements: Dict) -> Dict[str, str]:
        """
        Generate deployment configuration files.
        
        Args:
            code: Generated Python code
            requirements: Original requirements dictionary
            
        Returns:
            Dictionary with 'requirements', 'setup_instructions', 'github_push', and 'hosting_platforms' keys
        """
        req_text = self._format_requirements(requirements)
        
        log_agent_activity(logger, "DeploymentAgent", "Generating deployment config", {"code_length": len(code)})
        
        prompt = f"""Generate deployment configuration for the following Python project. Focus on simplicity and reproducibility.

ORIGINAL REQUIREMENTS:
{req_text}

GENERATED CODE:
```python
{code}
```

MANDATORY OUTPUTS:

1. **requirements.txt**:
   - Analyze the code to identify all Python dependencies
   - List all packages needed with appropriate versions
   - Include standard library imports (no need to list)
   - Format: package>=version or package==version
   - Be complete and accurate

2. **Project Setup Instructions**:
   - Step-by-step instructions for setting up the project locally
   - Include: Python version requirements, virtual environment setup, dependency installation
   - Make it simple, clear, and easy to follow
   - Ensure reproducibility (anyone can follow and get same result)
   - Include any environment variables or configuration needed

3. **GitHub Push Instructions**:
   - How to initialize a git repository: `git init`
   - How to create a .gitignore file (include common Python ignores: __pycache__, venv, .env, etc.)
   - How to add files: `git add .`
   - How to commit: `git commit -m "message"`
   - How to create a GitHub repository (via web interface)
   - How to add remote: `git remote add origin <repo-url>`
   - How to push: `git push -u origin main` or `git push -u origin master`
   - Provide complete step-by-step commands

4. **Hosting Platform Recommendations**:
   - Analyze the project type (web app, API, CLI tool, data processing, etc.)
   - Suggest 2-3 compatible hosting platforms
   - For each platform, explain:
     * Why it's suitable for this project
     * Key features that match the project needs
     * Brief deployment steps
   - Consider platforms like: Heroku, Railway, Render, Vercel, AWS, Google Cloud, Azure, DigitalOcean, etc.
   - Base recommendations on project characteristics (needs database, static files, API endpoints, etc.)

FOCUS ON:
- **Simplicity**: Instructions should be clear and easy to follow
- **Reproducibility**: Anyone following instructions should get the same working setup
- **Completeness**: Include all necessary steps

Format your response clearly with sections marked as:
[REQUIREMENTS]
[SETUP_INSTRUCTIONS]
[GITHUB_PUSH]
[HOSTING_PLATFORMS]"""
        
        log_api_call(logger, "DeploymentAgent", Config.MODEL, len(prompt))
        
        import time
        max_retries = 3
        content = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                if response is None:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"DeploymentAgent: None response on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise ValueError("Agent returned None response after retries. This may be due to API rate limiting or model unavailability.")
                
                content = response.get("content", "") if isinstance(response, dict) else str(response)
                
                if not content or not content.strip():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"DeploymentAgent: Empty response on attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise ValueError("Agent returned empty content after retries.")
                
                break  # Success, exit retry loop
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"DeploymentAgent: Error on attempt {attempt + 1}/{max_retries}: {str(e)}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"Deployment configuration API call failed after {max_retries} attempts: {str(e)}. Check API key, model configuration, and network connection.")
        
        if not content:
            error_msg = f"Failed to generate deployment configuration after {max_retries} attempts"
            if last_error:
                error_msg += f": {str(last_error)}"
            raise ValueError(error_msg)
        
        return self._parse_deployment_output(content)
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format requirements for deployment context."""
        text = "FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("functional_requirements", []):
            text += f"- {req}\n"
        
        return text
    
    def _parse_deployment_output(self, content: str) -> Dict[str, str]:
        """Parse the agent's output into structured deployment config."""
        requirements = ""
        setup_instructions = ""
        github_push = ""
        hosting_platforms = ""
        
        if "[REQUIREMENTS]" in content:
            req_start = content.find("[REQUIREMENTS]") + len("[REQUIREMENTS]")
            req_end = content.find("[SETUP_INSTRUCTIONS]", req_start)
            if req_end == -1:
                req_end = content.find("[GITHUB_PUSH]", req_start)
            if req_end > req_start:
                requirements = content[req_start:req_end].strip()
        
        if "[SETUP_INSTRUCTIONS]" in content:
            setup_start = content.find("[SETUP_INSTRUCTIONS]") + len("[SETUP_INSTRUCTIONS]")
            setup_end = content.find("[GITHUB_PUSH]", setup_start)
            if setup_end > setup_start:
                setup_instructions = content[setup_start:setup_end].strip()
        
        if "[GITHUB_PUSH]" in content:
            github_start = content.find("[GITHUB_PUSH]") + len("[GITHUB_PUSH]")
            github_end = content.find("[HOSTING_PLATFORMS]", github_start)
            if github_end > github_start:
                github_push = content[github_start:github_end].strip()
        
        if "[HOSTING_PLATFORMS]" in content:
            hosting_start = content.find("[HOSTING_PLATFORMS]") + len("[HOSTING_PLATFORMS]")
            hosting_platforms = content[hosting_start:].strip()
        
        if not requirements:
            requirements = self._generate_default_requirements()
        
        if not setup_instructions:
            setup_instructions = self._generate_default_setup()
        
        if not github_push:
            github_push = self._generate_default_github_push()
        
        if not hosting_platforms:
            hosting_platforms = self._generate_default_hosting_platforms()
        
        return {
            "requirements": requirements,
            "setup_instructions": setup_instructions,
            "github_push": github_push,
            "hosting_platforms": hosting_platforms,
        }
    
    def _generate_default_requirements(self) -> str:
        """Generate default requirements.txt if parsing fails."""
        return """python-dotenv>=1.0.0
pyautogen>=0.2.0
openai>=1.0.0
streamlit>=1.28.0
pytest>=7.4.0"""
    
    def _generate_default_setup(self) -> str:
        """Generate default setup instructions if parsing fails."""
        return """1. Install Python 3.10 or higher
2. Create a virtual environment: python -m venv venv
3. Activate the virtual environment:
   - Windows: venv\\Scripts\\activate
   - Linux/Mac: source venv/bin/activate
4. Install dependencies: pip install -r requirements.txt
5. Create a .env file with your OPENAI_API_KEY
6. Run the application: streamlit run app.py"""
    
    def _generate_default_github_push(self) -> str:
        """Generate default GitHub push instructions if parsing fails."""
        return """1. Initialize git repository:
   git init

2. Create .gitignore file with:
   __pycache__/
   *.pyc
   venv/
   .env
   *.log
   .DS_Store

3. Add files to git:
   git add .

4. Commit files:
   git commit -m "Initial commit"

5. Create a new repository on GitHub (via web interface)

6. Add remote repository:
   git remote add origin https://github.com/yourusername/your-repo-name.git

7. Push to GitHub:
   git branch -M main
   git push -u origin main"""
    
    def _generate_default_hosting_platforms(self) -> str:
        """Generate default hosting platform recommendations if parsing fails."""
        return """Recommended Hosting Platforms:

1. **Heroku**:
   - Suitable for: Web applications, APIs
   - Why: Easy deployment, free tier available, supports Python
   - Deployment: Use Heroku CLI or connect GitHub repository

2. **Railway**:
   - Suitable for: Web apps, APIs, databases
   - Why: Simple deployment, automatic builds from GitHub, good for Python projects
   - Deployment: Connect GitHub repo, auto-deploys on push

3. **Render**:
   - Suitable for: Web services, static sites, APIs
   - Why: Free tier, easy setup, supports Python
   - Deployment: Connect GitHub, automatic deployments"""

