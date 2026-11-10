import asyncio
from typing import Optional, Dict, Any

class BridgeState:
    def __init__(self):
        self.current_prompt: Optional[str] = None
        self.response_event = asyncio.Event()
        self.final_response: Optional[Dict[str, Any]] = None
        self.is_waiting: bool = False

# Singleton instance
state = BridgeState()