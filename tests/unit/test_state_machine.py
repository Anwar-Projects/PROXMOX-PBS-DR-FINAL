"""Unit tests for DR state machine."""

import pytest
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

from proxmox_dr.state_machine import (
    DRStateMachine,
    DRPhase,
    DREvent,
    DRContext,
    StateHandler,
)


@pytest.fixture
def state_machine():
    """Create a test state machine."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield DRStateMachine(
            state_file=f"{tmpdir}/state.json",
            history_file=f"{tmpdir}/history.jsonl",
        )


@pytest.fixture
def dr_context():
    """Create a test DR context."""
    return DRContext(
        dr_id="test-dr-001",
        start_time=datetime.now(),
        triggered_by="health_check",
    )


class TestDRStateMachine:
    """Tests for DRStateMachine."""
    
    def test_initial_state(self, state_machine):
        """Test initial state is IDLE."""
        assert state_machine.current_phase == DRPhase.IDLE
    
    def test_can_transition_valid(self, state_machine):
        """Test checking valid transitions."""
        assert state_machine.can_transition(DREvent.DISASTER_DETECTED) is True
        assert state_machine.can_transition(DREvent.HEALTH_CHECK_FAILED) is True
    
    def test_can_transition_invalid(self, state_machine):
        """Test checking invalid transitions."""
        # Can't go from IDLE directly to FAILOVER
        assert state_machine.can_transition(DREvent.FAILOVER_COMPLETE) is False
    
    @pytest.mark.asyncio
    async def test_trigger_event_success(self, state_machine, dr_context):
        """Test triggering a valid event."""
        result = await state_machine.trigger_event(
            DREvent.DISASTER_DETECTED, dr_context
        )
        assert result is True
        assert state_machine.current_phase == DRPhase.DETECT
    
    @pytest.mark.asyncio
    async def test_trigger_event_failure(self, state_machine, dr_context):
        """Test triggering an invalid event."""
        result = await state_machine.trigger_event(
            DREvent.FAILOVER_COMPLETE, dr_context
        )
        assert result is False
        assert state_machine.current_phase == DRPhase.IDLE
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, state_machine, dr_context):
        """Test a complete DR workflow."""
        # Detect disaster
        await state_machine.trigger_event(
            DREvent.DISASTER_DETECTED, dr_context
        )
        assert state_machine.current_phase == DRPhase.DETECT
        
        # Approve failover
        await state_machine.trigger_event(
            DREvent.FAILOVER_APPROVED, dr_context
        )
        assert state_machine.current_phase == DRPhase.DECIDE
        
        # Another approval to proceed
        await state_machine.trigger_event(
            DREvent.FAILOVER_APPROVED, dr_context
        )
        assert state_machine.current_phase == DRPhase.FAILOVER
        
        # Complete failover
        await state_machine.trigger_event(
            DREvent.FAILOVER_COMPLETE, dr_context
        )
        assert state_machine.current_phase == DRPhase.VERIFY
        
        # Pass verification
        await state_machine.trigger_event(
            DREvent.VERIFICATION_PASSED, dr_context
        )
        assert state_machine.current_phase == DRPhase.RESTORE
        
        # Complete restore
        await state_machine.trigger_event(
            DREvent.RESTORE_COMPLETE, dr_context
        )
        assert state_machine.current_phase == DRPhase.COMPLETED
    
    def test_reset(self, state_machine):
        """Test state reset."""
        state_machine.current_phase = DRPhase.FAILOVER
        state_machine.reset()
        assert state_machine.current_phase == DRPhase.IDLE
    
    def test_get_history_empty(self, state_machine):
        """Test getting history when empty."""
        history = state_machine.get_history()
        assert history == []
