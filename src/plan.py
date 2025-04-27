from src.model import PerceptionOutput
from src.model import PlanOutput
from typing import Optional, List
from src.memory_data import InteractionHistory
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def create_system_prompt(perception_output: PerceptionOutput, tools_description: List[str], interaction_history: List[InteractionHistory]) -> str:
    """
    Create a system prompt for the AI agent.
    """
    
    interaction_texts = "\n".join(f"{i+1}. {m.input_text}" for i, m in enumerate(interaction_history)) or "None"
                
    function_call = '{"response_type": "FUNCTION_CALL", "tool": "tool_name", "arguments": {"key1"="value1", "input2"= false, "input3"= 1.2, "input4": [1,2,3,4], "input5": ["A","B","C","D"]}, "reasoning_type": "type_of_reasoning"}'
    final_answer = '{"response_type": "FINAL_ANSWER", "final_answer": "text", "reasoning_type": "type_of_reasoning"}'
                
    example_step1 = '{"response_type": "FUNCTION_CALL", "tool": "search_documents", "arguments": {"query":"relationship between Cricket and Sachin Tendulkar"}, "reasoning_response_type": "lookup"}'
    example_step4 = '{"response_type": "FUNCTION_CALL", "tool": "strings_to_chars_to_int", "arguments": {"input":"INDIA"}, "reasoning_response_type": "lookup"}'
    example_step6 = '{"response_type": "FUNCTION_CALL", "tool": "verify_string_to_int", "arguments": {"expression":"INDIA", "expected": [73, 78, 68, 73, 65]}'
    example_step8 = '{"response_type": "FUNCTION_CALL", "tool": "int_list_to_exponential_sum", "arguments": {"int_list": [73, 78, 68, 73, 65]}, "reasoning_response_type": "arithmetic"}'
    example_step10 = '{"response_type": "FUNCTION_CALL", "tool": "verify_int_to_exponential_sum", "arguments": {"expression": [73, 78, 68, 73, 65], "expected": 7.59982224609308e+33}}'
    example_step12 = '{"response_type": "FUNCTION_CALL", "tool": "open_paint", "arguments": {}, "reasoning_response_type": "drawing"}'
    example_step14 = '{"response_type": "FUNCTION_CALL", "tool": "verify_open_paint", "arguments": {}}'
    example_step15 = '{"response_type": "FINAL_ANSWER", "final_answer": "4.515964472389928e+38", "reasoning_type": "arithmetic"}'

    system_prompt = f"""You are a reasoning-driven AI agent with access to tools. Your job is to solve the user's request step-by-step by reasoning through the problem, selecting a tool if needed, and continuing until the FINAL_ANSWER is produced.

You have access to the following available tools:
{tools_description}

Always follow this loop:
1. If a tool is needed, respond using the format:
{function_call}
2. When the final answer is known, respond using:
{final_answer}

Guidelines:
- Respond using EXACTLY ONE of the formats above per step.
- Do NOT wrap the json curly braces in ```json or other formatting.
- Do NOT include extra text, explanation, or formatting.
- Use nested keys (e.g., input.string) and square brackets for lists.

IMPORTANT:
- 🚫 Do NOT invent tools. Use only the tools listed below.
- 📄 If the question may relate to factual knowledge, use the 'search_documents' tool to look for the answer.
- 🧮 If the question is mathematical or needs calculation, use the appropriate math tool.
- 🤖 If the previous tool output already contains factual information, DO NOT search again. Instead, summarize the relevant facts and respond with: FINAL_ANSWER: [your answer]
- Only repeat `search_documents` if the last result was irrelevant or empty.
- ❌ Do NOT repeat function calls with the same parameters.
- ❌ Do NOT output unstructured responses.
- 🧠 Think before each step. Verify intermediate results mentally before proceeding.
- 💥 If unsure or no tool fits, skip to FINAL_ANSWER: [unknown]
- ✅ You have only 3 attempts. Final attempt must be FINAL_ANSWER]

Examples:
- {example_step1}
- {example_step4}
- {example_step6}
- {example_step8}
- {example_step10}
- {example_step12}
- {example_step14}
- {example_step15}

Original task: {perception_output.user_query}

You have already performed the following steps:
{interaction_texts}

Below is the input summary for next step:
- Intent: {perception_output.intent}
- Entities: {', '.join(perception_output.entities)}
- Tool hint: {perception_output.tool_hint or 'None'}
"""     
    return system_prompt


def get_plan(perception_output: PerceptionOutput, tools_descriptions: Optional[str], interaction_history: List[InteractionHistory]) -> PlanOutput:
    """
    Process the perception output and tools descriptions to create a plan output.
    """

    system_prompt = create_system_prompt(perception_output, tools_descriptions, interaction_history)
    #print("PLAN:", system_prompt)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=system_prompt
        )
        raw = response.text.strip()
        print("PLAN:", f"LLM Output: {raw}")

    except Exception as e:
        print("PLAN:", f"⚠️ Decision generation failed: {e}")
        return PlanOutput(response_type="ERROR:", tool="unknown", arguments={}, reasoning_type="error_handling")

    return PlanOutput.model_validate_json(raw)
