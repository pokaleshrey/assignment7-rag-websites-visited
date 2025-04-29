from google import genai
import json
from src.model import PerceptionOutput
from dotenv import load_dotenv
import os
import re
load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
def get_perception(user_query: str) -> PerceptionOutput:
    """Process the input data and generate content using Gemini."""
    
    try:
        prompt = f"""
You are an AI Agent that helps user to search a url, by matching user input text to indexed data.

Input: "{user_query}"

Return the response as a Python dictionary with keys:
- intent: (brief phrase about what the user wants)
- entities: a list of strings representing keywords or values (e.g., ["INDIA", "ASCII"]), use double quotes for strings
- tool_hint: (name of the MCP tool that might be useful, if any)

Important:
- Do NOT wrap the json curly braces in ```json or other formatting.
- Use double quotes for all keys in dictionary in output.
- Output only the dictionary on a single line. 
- Ensure `entities` is a list of strings, not a dictionary.

What should i do next ?
    """
        #print("PERCEPTION:", f"Prompt: {prompt}")
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        
        # Extract the text from the response's candidates field
        candidates = response.candidates
        if candidates and len(candidates) > 0:
            text = candidates[0].content.parts[0].text

            # Strip Markdown backticks if present
            clean = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()

            parsed_output = json.loads(clean)
            #print("PERCEPTION:", f"Parsed Output: {parsed_output}")
            # Create and return a PerceptionOutput object
            return PerceptionOutput(
                user_query=user_query,  # Set the user_query field
                intent=parsed_output.get("intent"),
                entities=parsed_output.get("entities"),
                tool_hint=parsed_output.get("tool_hint")
            )
        else:
            raise ValueError("No candidates found in the response.")
    
    except Exception as e:
        print("PERCEPTION:", f"⚠️ Extraction failed: {e}")
        return PerceptionOutput(user_query=user_query)