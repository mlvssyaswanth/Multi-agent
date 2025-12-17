"""
Documentation Agent - Generates comprehensive Markdown documentation.
"""
from typing import Dict
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class DocumentationAgent:
    """Agent responsible for generating project documentation."""
    
    def __init__(self):
        """Initialize the Documentation Agent."""
        self.agent = ConversableAgent(
            name="documentation_writer",
            system_message="""You are a technical documentation specialist with expertise in software documentation.

PRIMARY MISSION:
Generate clear, structured Markdown documentation for Python code.

MANDATORY SECTIONS (MUST BE INCLUDED):

1. **CODE OVERVIEW** (REQUIRED):
   - High-level description of what the code does
   - Purpose and main features
   - Key functionality summary
   - What problems it solves

2. **MODULE EXPLANATION** (REQUIRED):
   - Detailed explanation of each module/class
   - What each module does
   - How modules relate to each other
   - Module responsibilities and structure
   - If multiple files: explain each file's purpose

3. **FUNCTION DEFINITIONS** (REQUIRED):
   - Complete documentation for all functions and classes
   - Function/class names and descriptions
   - What each function does
   - How functions interact

4. **PARAMETERS AND RETURN TYPES** (REQUIRED):
   - For each function: list all parameters with their types
   - For each function: specify return type
   - Parameter descriptions and what they're used for
   - Default values if applicable
   - Exceptions that may be raised
   - Format: `function_name(param1: type, param2: type) -> return_type`

5. **USAGE EXAMPLES** (REQUIRED):
   - Practical, runnable code examples
   - Show how to use the code
   - Include example inputs and expected outputs
   - Multiple examples covering different use cases
   - Copy-paste ready code snippets

ADDITIONAL SECTIONS (if applicable):

6. **Setup and Installation**:
   - Prerequisites
   - Step-by-step LOCAL installation instructions
   - CRITICAL: DO NOT mention cloning repositories, git commands, or downloading from repositories
   - Provide instructions for setting up the newly generated code locally
   - Steps should include: creating the code file(s), installing dependencies, environment setup
   - Assume the generated code is available locally and needs to be set up

7. **How to Run the System**:
   - Command-line instructions
   - Required parameters
   - Example usage
   - Expected output

8. **Configuration** (if applicable):
   - Configuration options
   - Environment variables
   - Settings and their descriptions

DOCUMENTATION REQUIREMENTS:
- Write in clear, professional language
- Use proper Markdown formatting (headers ##, ###, code blocks, lists, tables)
- Make it suitable for both technical and non-technical audiences
- Ensure all five mandatory sections are present and comprehensive
- Code examples must be runnable and accurate
- Function signatures must include type information""",
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
    
    def generate_documentation(self, code: str, requirements: Dict) -> str:
        """
        Generate comprehensive documentation for the code.
        
        Args:
            code: Python code to document
            requirements: Original requirements dictionary
            
        Returns:
            Markdown documentation string
        """
        req_text = self._format_requirements(requirements)
        
        log_agent_activity(logger, "DocumentationAgent", "Generating documentation", {"code_length": len(code)})
        
        prompt = f"""Generate clear, structured Markdown documentation for the following Python code.

ORIGINAL REQUIREMENTS:
{req_text}

GENERATED CODE:
```python
{code}
```

MANDATORY SECTIONS (MUST BE INCLUDED):

1. **CODE OVERVIEW** (REQUIRED):
   - High-level description of what the code does
   - Purpose and main features
   - Key functionality summary
   - What problems it solves

2. **MODULE EXPLANATION** (REQUIRED):
   - Detailed explanation of each module/class
   - What each module does
   - How modules relate to each other
   - Module responsibilities and structure
   - If multiple files exist, explain each file's purpose

3. **FUNCTION DEFINITIONS** (REQUIRED):
   - Complete documentation for ALL functions and classes
   - Function/class names and descriptions
   - What each function does
   - How functions interact

4. **PARAMETERS AND RETURN TYPES** (REQUIRED):
   - For EACH function: list all parameters with their types
   - For EACH function: specify return type
   - Parameter descriptions and what they're used for
   - Default values if applicable
   - Exceptions that may be raised
   - Format example: `function_name(param1: type, param2: type) -> return_type`
   - Include type information for all parameters and return values

5. **USAGE EXAMPLES** (REQUIRED):
   - Practical, runnable code examples
   - Show how to use the code
   - Include example inputs and expected outputs
   - Multiple examples covering different use cases
   - Copy-paste ready code snippets
   - Examples should demonstrate actual usage

ADDITIONAL SECTIONS (include if applicable):

6. **Setup and Installation**:
   - Prerequisites
   - Step-by-step LOCAL installation instructions
   - CRITICAL: DO NOT mention cloning repositories, git commands, or downloading from repositories
   - Provide steps to set up the code that was just generated locally
   - Include: creating necessary files, installing dependencies, environment setup
   - Assume the code files are already available locally and need to be set up

7. **How to Run the System**:
   - Command-line instructions
   - Required parameters
   - Example usage
   - Expected output

8. **Configuration** (if applicable):
   - Configuration options
   - Environment variables
   - Settings and their descriptions

CRITICAL REQUIREMENTS:
- ALL FIVE mandatory sections (Code Overview, Module Explanation, Function Definitions, Parameters and Return Types, Usage Examples) MUST be included
- Function documentation must include complete parameter and return type information
- Usage examples must be runnable and accurate
- Use proper Markdown formatting (headers ##, ###, code blocks, lists)
- Write in clear, professional language
- Make documentation comprehensive and production-ready"""
        
        log_api_call(logger, "DocumentationAgent", Config.MODEL, len(prompt))
        
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        
        if response is None:
            raise ValueError("Agent returned None response. Check API key and model configuration.")
        
        documentation = response.get("content", "") if isinstance(response, dict) else str(response)
        
        return documentation
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format requirements for documentation context."""
        text = "FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("functional_requirements", []):
            text += f"- {req}\n"
        
        text += "\nNON-FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("non_functional_requirements", []):
            text += f"- {req}\n"
        
        return text

