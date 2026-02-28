"""Integration tests for DR scenarios."""

import pytest
import asyncio
from datetime import datetime

from proxmox_dr.state_machine import DRStateMachine, DRPhase, DREvent, DRContext
from proxmox_dr.orchestrator import DROrchestrator, WorkflowDAG, WorkflowNode, WorkflowStatus
from proxmox_dr.async_ops import BackupInfo, PBSBackupVerifier, ParallelVerifier


@pytest.fixture
def mock_workflow():
    """Create a simple mock workflow."""
    workflow = WorkflowDAG("test-workflow")
    
    async def mock_action():
        return "success"
    
    async def mock_rollback():
        return "rolled back"
    
    workflow.add_node(WorkflowNode(
        id="step1",
        name="Prepare",
        action=mock_action,
        rollback_action=mock_rollback,
    ))
    
    workflow.add_node(WorkflowNode(
        id="step2",
        name="Execute",
        action=mock_action,
        dependencies={"step1"},
    ))
    
    return workflow


class TestDRScenario:
    """Tests for DR scenarios."""
    
    @pytest.mark.asyncio
    async def test_simple_dr_workflow(self, mock_workflow):
        """Test a simple DR workflow execution."""
        state_machine = DRStateMachine()
        context = DRContext(
            dr_id="test-001",
            start_time=datetime.now(),
            triggered_by="test",
        )
        
        orchestrator = DROrchestrator(state_machine, dry_run=False)
        
        result = await orchestrator.execute_workflow(mock_workflow, context)
        assert result is True
        
        # Check all nodes completed
        for node in mock_workflow.nodes.values():
            assert node.status == WorkflowStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_dr_workflow_with_failure(self, mock_workflow):
        """Test DR workflow with a failed node."""
        
        async def failing_action():
            raise RuntimeError("Simulated failure")
        
        mock_workflow.nodes["step2"].action = failing_action
        
        state_machine = DRStateMachine()
        context = DRContext(
            dr_id="test-002",
            start_time=datetime.now(),
            triggered_by="test",
        )
        
        orchestrator = DROrchestrator(state_machine, dry_run=False)
        
        result = await orchestrator.execute_workflow(mock_workflow, context)
        assert result is False
        
        # Check step1 completed but step2 failed
        assert mock_workflow.nodes["step1"].status == WorkflowStatus.COMPLETED
        assert mock_workflow.nodes["step2"].status == WorkflowStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_dry_run_mode(self, mock_workflow):
        """Test dry-run mode doesn't execute actions."""
        
        action_executed = False
        
        async def tracking_action():
            nonlocal action_executed
            action_executed = True
            return "executed"
        
        mock_workflow.nodes["step1"].action = tracking_action
        
        state_machine = DRStateMachine()
        context = DRContext(
            dr_id="test-003",
            start_time=datetime.now(),
            triggered_by="test",
        )
        
        orchestrator = DROrchestrator(state_machine, dry_run=True)
        
        result = await orchestrator.execute_workflow(mock_workflow, context)
        assert result is True
        assert action_executed is False  # Dry run shouldn't execute


class TestDRStateMachine:
    """Tests for DR state machine integration."""
    
    @pytest.mark.asyncio
    async def test_state_machine_and_orchestrator(self):
        """Test integration between state machine and orchestrator."""
        state_machine = DRStateMachine()
        context = DRContext(
            dr_id="integration-001",
            start_time=datetime.now(),
            triggered_by="health_check",
        )
        
        # Trigger disaster detection
        await state_machine.trigger_event(
            DREvent.DISASTER_DETECTED, context
        )
        assert state_machine.current_phase == DRPhase.DETECT
        
        # Approve and proceed
        await state_machine.trigger_event(
            DREvent.FAILOVER_APPROVED, context
        )
        assert state_machine.current_phase == DRPhase.DECIDE
        
        # Check context is updated
        assert context.dr_id == "integration-001"
