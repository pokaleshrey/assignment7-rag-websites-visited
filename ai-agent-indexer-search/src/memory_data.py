from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InteractionHistory(BaseModel):
    """Store individual interaction details."""
    input_text: str = ""
    output_text: str = ""
    timestamp: Optional[str] = datetime.now().isoformat()


interaction_history: List[InteractionHistory] = []
user_query: str = ""
last_interaction: Optional[str] = None

def update_user_query(user_query) -> None:
    """Update the user query in memory."""
    user_query = user_query

def add_interaction(input_text: str, output_text: str) -> None:
    """Add a new interaction to history."""
    
    interaction = InteractionHistory(
        input_text=input_text,
        output_text=output_text,
        timestamp=datetime.now().isoformat()
    )
    interaction_history.append(interaction)
    last_interaction = interaction.timestamp

def get_recent_memory_interactions(limit: int = 50) -> List[InteractionHistory]:
    """Get most recent interactions."""
    return sorted(
        interaction_history,
        key=lambda x: x.timestamp,
        reverse=False
    )[:limit]

def clear_history() -> None:
    """Clear interaction history."""
    interaction_history.clear()