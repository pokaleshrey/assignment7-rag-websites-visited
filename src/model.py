from pydantic import BaseModel
from typing import Optional, List
from typing import Any, Dict

class PerceptionOutput(BaseModel):
    user_query: str
    entities: List[str]
    intent: Optional[str]
    tool_hint: Optional[str] = None

class PlanOutput(BaseModel):
    response_type: str
    tool: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    reasoning_type: Optional[str] = None
    final_answer: Optional[str] = None
    
class ActionOutput(BaseModel):
    arguments: Optional[Dict[str, Any]] = None
    tool: Optional[str] = None
    raw_response: str
    result: str
