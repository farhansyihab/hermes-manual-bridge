import asyncio
from typing import Optional, Dict, Any


class BridgeState:
    def __init__(self):
        # Prompt yang sedang diproses (bisa hasil edit user)
        self.current_prompt: Optional[str] = None
        # Prompt ASLI dari Hermes (sebelum diedit user) - untuk audit trail
        self.original_prompt: Optional[str] = None
        self.response_event = asyncio.Event()
        self.final_response: Optional[Dict[str, Any]] = None
        self.is_waiting: bool = False


# Singleton instance
state = BridgeState()