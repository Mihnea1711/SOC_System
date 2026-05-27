from typing import Callable, List, Dict, Any
from engine.utils.logger import logger

class NoiseFilterManager:
    """
    Manages a collection of noise filtering rules.
    
    This class implements a Chain of Responsibility pattern for filtering out
    background noise from raw Beats events before they are normalized and processed.
    If any registered rule returns True, the event is considered noise and should be dropped.
    """
    def __init__(self):
        self._rules: List[Callable[[Dict[str, Any]], bool]] = []
        logger.info("NoiseFilterManager initialized.")

    def register_rule(self, rule_func: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Registers a new filtering rule.
        
        Args:
            rule_func: A callable that takes a raw event dictionary and returns a boolean.
                       Returns True if the event is noise, False otherwise.
        """
        self._rules.append(rule_func)
        logger.debug(f"Registered noise filter rule: {rule_func.__name__}")

    def is_noise(self, event: Dict[str, Any]) -> bool:
        """
        Evaluates the event against all registered rules.
        
        Args:
            event: The raw JSON dictionary from Kafka (Packetbeat or Filebeat).
            
        Returns:
            True if ANY rule identifies the event as noise, False if it passes all rules.
        """
        for rule in self._rules:
            try:
                if rule(event):
                    # We don't log every dropped event here to save disk I/O, 
                    # but we could add a debug log if needed for troubleshooting.
                    return True
            except Exception:
                # If a rule fails (e.g., due to unexpected JSON structure), 
                # we log the error but do NOT drop the event, failing open.
                logger.exception(f"Error executing filter rule '{rule.__name__}'")
                
        return False
