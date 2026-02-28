"""DR State Machine for orchestrating disaster recovery phases.

Implements a finite state machine for DR phases:
detect → decide → failover → verify → restore
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DRPhase(Enum):
    """DR state machine phases."""
    IDLE = "idle"
    DETECT = "detect"           # Detect disaster/health issues
    DECIDE = "decide"           # Make failover decision
    FAILOVER = "failover"       # Execute failover
    VERIFY = "verify"           # Verify failover success
    RESTORE = "restore"         # Restore services
    ROLLBACK = "rollback"       # Rollback on failure
    COMPLETED = "completed"     # DR completed successfully
    FAILED = "failed"           # DR failed


class DREvent(Enum):
    """Events that trigger state transitions."""
    DISASTER_DETECTED = auto()
    HEALTH_CHECK_FAILED = auto()
    FAILOVER_APPROVED = auto()
    FAILOVER_DENIED = auto()
    FAILOVER_COMPLETE = auto()
    VERIFICATION_PASSED = auto()
    VERIFICATION_FAILED = auto()
    RESTORE_COMPLETE = auto()
    ROLLBACK_TRIGGERED = auto()
    ROLLBACK_COMPLETE = auto()
    TIMEOUT = auto()
    MANUAL_OVERRIDE = auto()


@dataclass
class StateTransition:
    """Represents a state transition."""
    from_phase: DRPhase
    to_phase: DRPhase
    event: DREvent
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DRContext:
    """Context for DR operations."""
    dr_id: str
    start_time: datetime
    triggered_by: str
    pbs_main_status: str = "unknown"
    pbs_dr_status: str = "unknown"
    failover_target: Optional[str] = None
    verification_results: List[Dict] = field(default_factory=list)
    restore_status: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateHandler(ABC):
    """Abstract base class for state handlers."""
    
    @abstractmethod
    async def on_enter(self, context: DRContext) -> None:
        """Called when entering the state."""
        pass
    
    @abstractmethod
    async def on_exit(self, context: DRContext) -> None:
        """Called when exiting the state."""
        pass
    
    @abstractmethod
    async def handle_event(
        self,
        event: DREvent,
        context: DRContext,
    ) -> Optional[DRPhase]:
        """Handle an event, return next phase or None."""
        pass


class DRStateMachine:
    """State machine for DR orchestration."""
    
    # Define valid transitions
    TRANSITIONS: Dict[Tuple[DRPhase, DREvent], DRPhase] = {
        (DRPhase.IDLE, DREvent.DISASTER_DETECTED): DRPhase.DETECT,
        (DRPhase.IDLE, DREvent.HEALTH_CHECK_FAILED): DRPhase.DETECT,
        (DRPhase.IDLE, DREvent.MANUAL_OVERRIDE): DRPhase.DETECT,
        
        (DRPhase.DETECT, DREvent.FAILOVER_APPROVED): DRPhase.DECIDE,
        (DRPhase.DETECT, DREvent.FAILOVER_DENIED): DRPhase.IDLE,
        (DRPhase.DETECT, DREvent.TIMEOUT): DRPhase.FAILED,
        
        (DRPhase.DECIDE, DREvent.FAILOVER_APPROVED): DRPhase.FAILOVER,
        (DRPhase.DECIDE, DREvent.FAILOVER_DENIED): DRPhase.IDLE,
        
        (DRPhase.FAILOVER, DREvent.FAILOVER_COMPLETE): DRPhase.VERIFY,
        (DRPhase.FAILOVER, DREvent.VERIFICATION_FAILED): DRPhase.ROLLBACK,
        (DRPhase.FAILOVER, DREvent.TIMEOUT): DRPhase.ROLLBACK,
        
        (DRPhase.VERIFY, DREvent.VERIFICATION_PASSED): DRPhase.RESTORE,
        (DRPhase.VERIFY, DREvent.VERIFICATION_FAILED): DRPhase.ROLLBACK,
        
        (DRPhase.RESTORE, DREvent.RESTORE_COMPLETE): DRPhase.COMPLETED,
        (DRPhase.RESTORE, DREvent.VERIFICATION_FAILED): DRPhase.ROLLBACK,
        
        (DRPhase.ROLLBACK, DREvent.ROLLBACK_COMPLETE): DRPhase.FAILED,
        (DRPhase.ROLLBACK, DREvent.MANUAL_OVERRIDE): DRPhase.IDLE,
    }
    
    def __init__(
        self,
        state_file: Optional[str] = None,
        history_file: Optional[str] = None,
    ):
        self.current_phase = DRPhase.IDLE
        self.state_file = state_file or "/var/lib/proxmox-dr/state.json"
        self.history_file = history_file or "/var/lib/proxmox-dr/history.jsonl"
        self.transitions: List[StateTransition] = []
        self.handlers: Dict[DRPhase, StateHandler] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load state from file."""
        if Path(self.state_file).exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.current_phase = DRPhase(data.get('phase', 'idle'))
                    logger.info(f"Loaded state: {self.current_phase.value}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self) -> None:
        """Save state to file."""
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                'phase': self.current_phase.value,
                'timestamp': datetime.now().isoformat(),
            }, f)
    
    def _log_transition(self, transition: StateTransition) -> None:
        """Log transition to history file."""
        Path(self.history_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'a') as f:
            f.write(json.dumps({
                'from': transition.from_phase.value,
                'to': transition.to_phase.value,
                'event': transition.event.name,
                'timestamp': transition.timestamp.isoformat(),
                'metadata': transition.metadata,
            }) + '\n')
    
    def register_handler(self, phase: DRPhase, handler: StateHandler) -> None:
        """Register a handler for a phase."""
        self.handlers[phase] = handler
    
    def can_transition(self, event: DREvent) -> bool:
        """Check if a transition is valid."""
        return (self.current_phase, event) in self.TRANSITIONS
    
    async def trigger_event(
        self,
        event: DREvent,
        context: DRContext,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Trigger a state transition event.
        
        Args:
            event: The event to trigger
            context: DR context
            metadata: Optional metadata for the transition
            
        Returns:
            True if transition succeeded, False otherwise
        """
        key = (self.current_phase, event)
        if key not in self.TRANSITIONS:
            logger.warning(
                f"Invalid transition: {self.current_phase.value} -> {event.name}"
            )
            return False
        
        next_phase = self.TRANSITIONS[key]
        
        # Call on_exit for current phase
        if self.current_phase in self.handlers:
            await self.handlers[self.current_phase].on_exit(context)
        
        # Record transition
        transition = StateTransition(
            from_phase=self.current_phase,
            to_phase=next_phase,
            event=event,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self.transitions.append(transition)
        self._log_transition(transition)
        
        # Update state
        self.current_phase = next_phase
        self._save_state()
        
        # Call on_enter for new phase
        if self.current_phase in self.handlers:
            await self.handlers[self.current_phase].on_enter(context)
        
        logger.info(f"Transitioned to {self.current_phase.value}")
        return True
    
    async def run_phase_handler(
        self,
        event: DREvent,
        context: DRContext,
    ) -> Optional[DRPhase]:
        """Run the handler for the current phase.
        
        Args:
            event: The event to handle
            context: DR context
            
        Returns:
            Next phase or None if no transition
        """
        if self.current_phase in self.handlers:
            return await self.handlers[self.current_phase].handle_event(
                event, context
            )
        return None
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transition history."""
        if not Path(self.history_file).exists():
            return []
        
        history = []
        with open(self.history_file, 'r') as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
        
        return history[-limit:]
    
    def reset(self) -> None:
        """Reset state machine to IDLE."""
        self.current_phase = DRPhase.IDLE
        self._save_state()
        logger.info("State machine reset to IDLE")
