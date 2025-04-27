from mcp import ClientSession
from src.model import PlanOutput
from mcp.types import TextContent
from src.model import ActionOutput


async def execute_action(plan_output:PlanOutput, session:ClientSession) -> TextContent:
    print(f"ACTION: Calling tool {plan_output.tool} with arguments: {plan_output.arguments}")
    
    result = await session.call_tool(plan_output.tool, arguments=plan_output.arguments)
    #print(f"ACTION: LLM Output: {result}")
    
    # Get the full result content
    if hasattr(result, 'content'):
        # Handle multiple content items
        if isinstance(result.content, list):
            iteration_result = [
                item.text if hasattr(item, 'text') else str(item)
                for item in result.content
            ]
            #print(f"ACTION: LLM Output {iteration_result}")
        else:
            iteration_result = str(result.content)
    else:
        print(f"ACTION: Result has no content attribute")
        iteration_result = str(result)
    
    return ActionOutput(
        arguments=plan_output.arguments,
        tool=plan_output.tool,
        raw_response=str(result),
        result=str(iteration_result)
    )
