from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from src.memory_data import update_user_query, get_recent_memory_interactions, add_interaction
from src.perception import get_perception
from src.plan import get_plan
from src.action import execute_action
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class InputSearchQuery(BaseModel):
    query: str

@app.get("/search-text")
async def search_text(query: str = Query(..., description="Search query")):
    if not query:
        raise HTTPException(status_code=400, detail="'query' is required")

    # Pass the query to process_documents
    print("INFO", f"Processing query: {query}")
    response_data = await main(query)
    if response_data is None:
        raise HTTPException(status_code=500, detail="Failed to process the query. Response data is None.")

    url = response_data.get("url")
    highlight_text = response_data.get("highlight_text")

    response = {
        "query": query,
        "url": url,
        "highlight_text": highlight_text
    }
    return response

async def main(query: str) -> Dict[str, Any]:
    print("ASSISTANT:", "Starting main execution...")
    try:
        # Create a single MCP server connection
        print("ASSISTANT:", "Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["src/mcp_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("ASSISTANT:", "Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("ASSISTANT:", "Session created, initializing...")
                await session.initialize()
                
                user_query = query
                
                update_user_query(user_query)
                print("ASSISTANT:", "-" * 50)

                # Get available tools
                tools_result = await session.list_tools()
                tools = tools_result.tools
                tools_descriptions = "\n".join(
                                f"- {tool.name}: {getattr(tool, 'description', 'No description')}" 
                                for tool in tools
                            )
                print("ASSISTANT:", f"Successfully retrieved {len(tools)} tools")
                
                max_iterations = 15
                iteration = 0

                while iteration < max_iterations:
                    print("ASSISTANT:", f"--- Iteration {iteration + 1} ---")
                   
                    # Perception
                    perception_output = get_perception(user_query)
                    print("ASSISTANT:", f"Perception Output: {perception_output}")

                    # Get Latest interaction in memory
                    recent_memory_interactions = get_recent_memory_interactions(limit=20)
                    print("ASSISTANT:", f"Recent Interactions fetched: {len(recent_memory_interactions)}")

                    # Plan
                    plan_output = get_plan(perception_output, tools_descriptions, recent_memory_interactions)
                    print("ASSISTANT:", f"Plan Output: {plan_output}")

                    if plan_output.response_type == "FINAL_ANSWER":
                        print("ASSISTANT:", f"✅ FINAL RESULT: {plan_output}")
                        return plan_output.arguments

                    try:
                        # Action
                        action_output = await execute_action(plan_output, session)
                        print("ASSISTANT:", f"Action Output: {action_output}")

                        add_interaction(input_text=f"Tool call: {action_output.tool} with {action_output.arguments}, got: {action_output.result}", 
                                                     output_text=action_output.result)
                        print("ASSISTANT:", f"Memory updated with action output: {action_output.result}")

                        user_query = f"{query} \n You have called a tool {action_output.tool} with arguments {action_output.arguments}, result is: {action_output.result}."

                    except Exception as e:
                        print("ASSISTANT:", f"Failed to get LLM response: {e}")
                        break

                    iteration += 1

    except Exception as e:
        print("ASSISTANT:", f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print("ASSISTANT:", "\nGoodbye!")

# if __name__ == "__main__":
#     query = input("\nEnter your query or Press Enter for default one: ").strip()
#     query = query if query else "What do you know about Don Tapscott and Anthony Williams?"
#     asyncio.run(main(query))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8081, 
        reload=True
    )