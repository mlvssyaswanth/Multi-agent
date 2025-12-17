"""
Requirement Analysis Agent - Converts natural language to structured requirements.
Detects ambiguity and asks clarifying questions.
"""
import json
import re
from typing import Dict, Any, List, Optional
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class RequirementAnalysisAgent:
    """Agent responsible for analyzing and structuring user requirements."""
    
    def __init__(self):
        """Initialize the Requirement Analysis Agent."""
        self.agent = ConversableAgent(
            name="requirement_analyst",
            system_message="""You are a Senior Requirements Analyst specializing in software engineering.
Your task is to analyze natural language requirements and convert vague, ambiguous inputs into structured, actionable software requirements.

CRITICAL CAPABILITIES:
1. **Ambiguity Detection**: Identify vague terms, missing details, unclear specifications
2. **Clarifying Questions**: Generate specific questions to resolve ambiguity (even if simulated/answered automatically)
3. **Structured Output**: Convert requirements into clear, structured format

OUTPUT FORMAT:
You must output a JSON object with the following structure:
{
    "functional_requirements": ["list of specific, testable functional requirements"],
    "non_functional_requirements": ["list of non-functional requirements (performance, security, usability, etc.)"],
    "assumptions": ["list of assumptions made when requirements are vague"],
    "constraints": ["list of constraints identified (technical, business, time, etc.)"],
    "clarifying_questions": ["list of questions to resolve ambiguity - even if simulated"],
    "ambiguity_detected": true/false,
    "ambiguity_notes": "description of detected ambiguities and how they were resolved"
}

AMBIGUITY DETECTION:
Look for:
- Vague terms: "user-friendly", "fast", "good", "easy", "simple"
- Missing specifications: no input/output formats, no error handling mentioned, no UI details
- Unclear scope: "some features", "various operations", "multiple ways"
- Missing constraints: no performance requirements, no platform specified, no security mentioned
- Unclear user roles: who are the users? what permissions?

CLARIFYING QUESTIONS:
When ambiguity is detected, generate specific questions such as:
- "What specific input format should be accepted?"
- "What are the performance requirements (response time, throughput)?"
- "What platform should this run on?"
- "Who are the target users?"
- "What error handling is expected?"
- "What is the expected output format?"

Be thorough, specific, and ensure all requirements are testable and implementable.
Focus on clarity, completeness, and identifying all ambiguities.""",
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
    
    def analyze(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze user input and return structured requirements.
        Detects ambiguity and generates clarifying questions.
        
        Args:
            user_input: Natural language description of requirements
            context: Optional context dictionary containing previous prompts and results for follow-up prompts
            
        Returns:
            Dictionary containing structured requirements with ambiguity detection
        """
        log_agent_activity(logger, "RequirementAnalysisAgent", "Starting analysis", {"input_length": len(user_input), "has_context": context is not None})
        
        # First, detect ambiguity
        ambiguity_info = self._detect_ambiguity(user_input)
        
        # Build context information if available
        context_section = ""
        if context and context.get("is_active"):
            previous_prompts = context.get("previous_prompts", [])
            previous_results = context.get("previous_results")
            
            if previous_prompts or previous_results:
                context_section = "\n\nPREVIOUS CONTEXT:\n"
                if previous_prompts:
                    context_section += f"Previous prompt(s): {previous_prompts[-1]}\n"
                if previous_results:
                    prev_reqs = previous_results.get("requirements", {})
                    if prev_reqs:
                        context_section += f"Previous functional requirements: {', '.join(prev_reqs.get('functional_requirements', [])[:3])}\n"
                    prev_code = previous_results.get("code", "")
                    if prev_code:
                        code_summary = prev_code[:200] + "..." if len(prev_code) > 200 else prev_code
                        context_section += f"Previous code summary: {code_summary}\n"
                context_section += "\nThis is a follow-up request. Please update/modify the requirements based on the new input while maintaining consistency with the previous context.\n"
        
        prompt = f"""Analyze the following user requirement and convert vague natural language into structured, actionable software requirements.
{context_section}
USER REQUIREMENT:
{user_input}

TASK:
1. **Detect Ambiguity**: Identify vague terms, missing details, unclear specifications
2. **Generate Clarifying Questions**: Create specific questions to resolve any ambiguity (even if simulated/answered automatically)
3. **Convert to Structured Requirements**: Transform the requirement into clear, testable requirements

OUTPUT FORMAT:
Provide your analysis as a JSON object with this exact structure:
{{
    "functional_requirements": ["specific, testable functional requirements"],
    "non_functional_requirements": ["non-functional requirements (performance, security, usability, scalability, etc.)"],
    "assumptions": ["assumptions made when requirements are vague or incomplete"],
    "constraints": ["constraints identified (technical, business, time, platform, etc.)"],
    "clarifying_questions": ["specific questions to resolve ambiguity - generate even if simulated"],
    "ambiguity_detected": true/false,
    "ambiguity_notes": "description of detected ambiguities and how assumptions were made to resolve them"
}}

IMPORTANT:
- If ambiguity is detected, generate clarifying questions AND make reasonable assumptions
- Document all assumptions clearly
- Ensure functional requirements are specific and testable
- Include non-functional requirements even if not explicitly mentioned (make reasonable assumptions)
- Be thorough and comprehensive"""
        
        log_api_call(logger, "RequirementAnalysisAgent", Config.MODEL, len(prompt))
        
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        
        if response is None:
            logger.error("Agent returned None response")
            raise ValueError("Agent returned None response. Check API key and model configuration.")
        
        content = response.get("content", "") if isinstance(response, dict) else str(response)
        log_api_call(logger, "RequirementAnalysisAgent", Config.MODEL, len(prompt), len(content))
        
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                requirements = json.loads(json_str)
            else:
                requirements = self._parse_fallback(content)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {str(e)}, using fallback parser")
            requirements = self._parse_fallback(content)
        
        # Ensure all required fields are present
        result = {
            "functional_requirements": requirements.get("functional_requirements", []),
            "non_functional_requirements": requirements.get("non_functional_requirements", []),
            "assumptions": requirements.get("assumptions", []),
            "constraints": requirements.get("constraints", []),
            "clarifying_questions": requirements.get("clarifying_questions", []),
            "ambiguity_detected": requirements.get("ambiguity_detected", False),
            "ambiguity_notes": requirements.get("ambiguity_notes", ""),
        }
        
        if result["ambiguity_detected"]:
            logger.info(f"Ambiguity detected, {len(result['clarifying_questions'])} questions generated")
        
        return result
    
    def _detect_ambiguity(self, user_input: str) -> Dict[str, Any]:
        """
        Detect ambiguity in user input using pattern matching.
        
        Args:
            user_input: Natural language requirement
            
        Returns:
            Dictionary with ambiguity detection results
        """
        vague_terms = [
            r'\b(user-friendly|user friendly)\b',
            r'\b(fast|quick|quickly)\b',
            r'\b(good|better|best)\b',
            r'\b(easy|simple|easily)\b',
            r'\b(nice|nice-looking|pretty)\b',
            r'\b(some|various|multiple|several)\b',
            r'\b(should|could|might|may)\b',
        ]
        
        missing_patterns = [
            r'\b(input|output)\b',  # Check if input/output formats are mentioned
            r'\b(error|exception|handle)\b',  # Check if error handling is mentioned
            r'\b(platform|os|operating system)\b',  # Check if platform is specified
            r'\b(performance|speed|time)\b',  # Check if performance is mentioned
        ]
        
        vague_count = sum(1 for pattern in vague_terms if re.search(pattern, user_input, re.IGNORECASE))
        missing_count = sum(1 for pattern in missing_patterns if not re.search(pattern, user_input, re.IGNORECASE))
        
        is_ambiguous = vague_count > 2 or missing_count > 2 or len(user_input.strip()) < 50
        
        return {
            "is_ambiguous": is_ambiguous,
            "vague_terms_found": vague_count,
            "missing_specifications": missing_count,
            "input_length": len(user_input),
        }
    
    def _parse_fallback(self, content: str) -> Dict[str, Any]:
        """Fallback parser if JSON extraction fails."""
        return {
            "functional_requirements": [content],
            "non_functional_requirements": [],
            "assumptions": ["Could not parse structured requirements - using raw input"],
            "constraints": [],
            "clarifying_questions": [],
            "ambiguity_detected": True,
            "ambiguity_notes": "JSON parsing failed - requirements may be incomplete",
        }

