"""
Test Case Generation Agent - Generates executable pytest test cases.
"""
from typing import Dict
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class TestGenerationAgent:
    """Agent responsible for generating executable pytest test cases."""
    
    def __init__(self):
        """Initialize the Test Generation Agent."""
        self.agent = ConversableAgent(
            name="test_generator",
            system_message="""You are a Senior Test Engineer specializing in Python unit testing with pytest.

PRIMARY MISSION:
Generate unit tests that are pytest-compatible, executable without modification, with at least one test per module.

CORE RESPONSIBILITIES:
1. **Generate Unit Tests**: Create unit tests (not integration or end-to-end tests)
2. **At Least One Test Per Module**: MANDATORY - Create at least one test case per module/class/function
3. **pytest-Compatible**: Generate test files that are fully compatible with pytest framework
4. **Executable Without Modification**: Tests must be immediately runnable with pytest without any changes

MANDATORY REQUIREMENTS:

1. **UNIT TESTS**:
   - Generate unit tests (test individual functions, methods, classes in isolation)
   - Test one unit of code at a time
   - Use mocks/fixtures where appropriate to isolate units
   - Focus on testing individual components, not full system integration

2. **AT LEAST ONE TEST PER MODULE**:
   - Identify ALL modules, classes, and functions in the code
   - Generate a MINIMUM of one test for each identified component
   - If code has multiple classes, test each class
   - If code has multiple functions, test each function
   - If code has multiple modules (separate files), ensure tests for each module
   - Group related tests by module/class using test classes or clear naming

3. **PYTEST-COMPATIBLE TEST FILES**:
   - Use proper pytest syntax (test functions starting with `test_`)
   - Use pytest assertions (`assert` statements)
   - Use pytest fixtures if needed (`@pytest.fixture`)
   - Use pytest parametrization if appropriate (`@pytest.mark.parametrize`)
   - Use pytest exception testing (`pytest.raises()`)
   - Follow pytest naming conventions (test files: `test_*.py`, test functions: `test_*`)
   - Import pytest properly: `import pytest`
   - Use pytest-compatible imports and structure

4. **EXECUTABLE WITHOUT MODIFICATION**:
   - All imports must be correct and available
   - No placeholders, TODOs, or incomplete tests
   - All test code must be syntactically correct
   - Tests must run with `pytest` command without any code changes
   - Import statements must match the actual code structure
   - Test data must be self-contained or properly mocked
   - No missing dependencies or undefined variables

TEST REQUIREMENTS:
- Use proper pytest syntax and assertions
- Include descriptive test names that indicate what module/function is being tested
- Test both success and failure scenarios
- Cover normal cases, edge cases, and error scenarios
- For each test, include a comment showing expected execution result
- Test actual code execution, not just imports
- Use pytest best practices (fixtures, parametrization where appropriate)

OUTPUT FORMAT:
- Python test code fully compatible with pytest
- Include execution results as comments after each test
- Format: # Expected Result: [description of what should happen]
- Organize tests by module/class for clarity
- Ready to run with: `pytest test_file.py`

Example:
```python
import pytest

# Unit tests for calculator module
def test_calculator_addition():
    """Test addition function."""
    result = add(2, 3)
    assert result == 5
    # Expected Result: Test passes, returns 5

def test_calculator_division():
    """Test division function."""
    result = divide(10, 2)
    assert result == 5
    # Expected Result: Test passes, returns 5

def test_calculator_division_by_zero():
    """Test division by zero raises ValueError."""
    with pytest.raises(ValueError):
        divide(10, 0)
    # Expected Result: Test passes, ValueError raised correctly
```

Output only the Python test code, properly formatted and ready for execution with pytest.""",
            llm_config={
                "config_list": [{
                    "model": Config.MODEL,
                    "api_key": Config.OPENAI_API_KEY,
                    "temperature": Config.TEMPERATURE,
                }],
                "timeout": 180,
            },
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
        )
    
    def generate_tests(self, code: str, requirements: Dict) -> str:
        """
        Generate pytest test cases for the given code.
        
        Args:
            code: Python code to test
            requirements: Original requirements dictionary
            
        Returns:
            Generated pytest test code as string
        """
        req_text = self._format_requirements(requirements)
        
        log_agent_activity(logger, "TestGenerationAgent", "Generating test cases", {"code_length": len(code)})
        
        # Analyze code to identify modules/classes/functions
        modules_info = self._identify_modules(code)
        
        prompt = f"""Generate unit tests for the following Python code. Tests must be pytest-compatible and executable without modification.

ORIGINAL REQUIREMENTS:
{req_text}

CODE TO TEST:
```python
{code}
```

IDENTIFIED MODULES/CLASSES/FUNCTIONS:
{modules_info}

MANDATORY REQUIREMENTS:

1. **GENERATE UNIT TESTS**:
   - Create unit tests (test individual functions, methods, classes in isolation)
   - Test one unit of code at a time
   - Use mocks/fixtures where appropriate to isolate units
   - Focus on testing individual components

2. **AT LEAST ONE TEST PER MODULE** (MANDATORY):
   - **You MUST create at least one test for each module/class/function identified above**
   - If multiple modules/classes/functions exist, ensure each has at least one test
   - Test all major functions and classes
   - Group related tests by module/class

3. **PYTEST-COMPATIBLE TEST FILES**:
   - Use proper pytest syntax (test functions starting with `test_`)
   - Use pytest assertions (`assert` statements)
   - Import pytest: `import pytest`
   - Use pytest.raises() for exception testing
   - Follow pytest naming conventions
   - Use pytest fixtures if needed
   - Ensure full pytest compatibility

4. **EXECUTABLE WITHOUT MODIFICATION**:
   - All imports must be correct and match the actual code structure
   - No placeholders, TODOs, or incomplete tests
   - All test code must be syntactically correct
   - Tests must run with `pytest` command without any code changes
   - Test data must be self-contained or properly mocked
   - No missing dependencies or undefined variables

ADDITIONAL REQUIREMENTS:
- Cover normal cases, edge cases, and error scenarios
- Include descriptive test names that indicate which module/function is being tested
- Include execution results as comments showing what each test should produce
- Test the actual execution of the code, not just imports
- Include both positive and negative test cases
- Make tests comprehensive and realistic

For each test function, add a comment showing the expected execution result, for example:
# Expected Result: Test passes, function returns correct value
# Expected Result: Test passes, exception is raised correctly

CRITICAL: 
- **You MUST create at least one unit test for each module/class/function identified**
- Tests must be pytest-compatible and runnable with `pytest` without modification
- All imports and dependencies must be correct
- Tests must be complete and functional

Output only the Python test code, properly formatted, pytest-compatible, and ready for execution."""
        
        log_api_call(logger, "TestGenerationAgent", Config.MODEL, len(prompt))
        
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        
        if response is None:
            raise ValueError("Agent returned None response. Check API key and model configuration.")
        
        test_code = response.get("content", "") if isinstance(response, dict) else str(response)
        test_code = self._extract_code_blocks(test_code)
        
        return test_code
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format requirements for test generation context."""
        text = "FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("functional_requirements", []):
            text += f"- {req}\n"
        
        text += "\nNON-FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("non_functional_requirements", []):
            text += f"- {req}\n"
        
        return text
    
    def _identify_modules(self, code: str) -> str:
        """
        Identify modules, classes, and functions in the code.
        
        Args:
            code: Python code string
            
        Returns:
            Formatted string listing identified modules/classes/functions
        """
        import re
        import ast
        
        modules_info = []
        
        try:
            # Try to parse the code as AST
            tree = ast.parse(code)
            
            # Find all classes
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            
            # Find all function definitions (not methods)
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if it's a top-level function (not inside a class)
                    parent = None
                    for parent_node in ast.walk(tree):
                        if isinstance(parent_node, (ast.ClassDef, ast.FunctionDef)):
                            for child in ast.iter_child_nodes(parent_node):
                                if child == node:
                                    parent = parent_node
                                    break
                    if not isinstance(parent, ast.ClassDef):
                        functions.append(node.name)
            
            if classes:
                modules_info.append(f"Classes found: {', '.join(classes)}")
            if functions:
                modules_info.append(f"Top-level functions found: {', '.join(functions)}")
            
            # Also check for multiple files pattern
            if "# File:" in code or "## File:" in code:
                file_pattern = r'#+\s*File:\s*([^\n]+\.py)'
                files = re.findall(file_pattern, code)
                if files:
                    modules_info.append(f"Files found: {', '.join(files)}")
            
        except SyntaxError:
            # If AST parsing fails, use regex fallback
            # Find class definitions
            class_pattern = r'^class\s+(\w+)'
            classes = re.findall(class_pattern, code, re.MULTILINE)
            if classes:
                modules_info.append(f"Classes found: {', '.join(classes)}")
            
            # Find function definitions (not indented)
            func_pattern = r'^def\s+(\w+)\s*\('
            functions = re.findall(func_pattern, code, re.MULTILINE)
            if functions:
                modules_info.append(f"Top-level functions found: {', '.join(functions)}")
            
            # Check for multiple files
            if "# File:" in code or "## File:" in code:
                file_pattern = r'#+\s*File:\s*([^\n]+\.py)'
                files = re.findall(file_pattern, code)
                if files:
                    modules_info.append(f"Files found: {', '.join(files)}")
        
        if not modules_info:
            modules_info.append("Single module detected (no explicit classes or multiple files found)")
        
        return "\n".join(modules_info) if modules_info else "Code structure analysis completed"
    
    def _extract_code_blocks(self, content: str) -> str:
        """Extract Python code from markdown code blocks."""
        if "```python" in content:
            start = content.find("```python") + 9
            end = content.find("```", start)
            return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            return content[start:end].strip()
        return content.strip()

