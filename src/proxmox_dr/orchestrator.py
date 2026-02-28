"""DR Orchestrator with workflow DAG support.

Manages complex multi-node recovery workflows with rollback capability.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .state_machine import DRStateMachine, DRPhase, DREvent, DRContext

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow node."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """A node in the workflow DAG."""
    id: str
    name: str
    action: Callable[[], Any]
    rollback_action: Optional[Callable[[], Any]] = None
    dependencies: Set[str] = field(default_factory=set)
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_retries: int = 3
    timeout_seconds: int = 300


class WorkflowDAG:
    """Directed Acyclic Graph for DR workflows."""
    
    def __init__(self, name: str):
        self.name = name
        self.nodes: Dict[str, WorkflowNode] = {}
        self._lock = asyncio.Lock()
    
    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the DAG."""
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists")
        self.nodes[node.id] = node
    
    def add_dependency(self, node_id: str, depends_on: str) -> None:
        """Add a dependency between nodes."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        if depends_on not in self.nodes:
            raise ValueError(f"Dependency {depends_on} not found")
        self.nodes[node_id].dependencies.add(depends_on)
    
    def get_ready_nodes(self) -> List[WorkflowNode]:
        """Get nodes that are ready to execute (dependencies met)."""
        ready = []
        for node in self.nodes.values():
            if node.status != WorkflowStatus.PENDING:
                continue
            deps_met = all(
                self.nodes[dep].status == WorkflowStatus.COMPLETED
                for dep in node.dependencies
            )
            if deps_met:
                ready.append(node)
        return ready
    
    def is_complete(self) -> bool:
        """Check if all nodes are complete."""
        return all(
            node.status in (WorkflowStatus.COMPLETED, WorkflowStatus.SKIPPED)
            for node in self.nodes.values()
        )
    
    def has_failures(self) -> bool:
        """Check if any node failed."""
        return any(
            node.status == WorkflowStatus.FAILED
            for node in self.nodes.values()
        )
    
    def get_failed_nodes(self) -> List[WorkflowNode]:
        """Get all failed nodes."""
        return [
            node for node in self.nodes.values()
            if node.status == WorkflowStatus.FAILED
        ]


class DROrchestrator:
    """Orchestrates disaster recovery workflows."""
    
    def __init__(
        self,
        state_machine: DRStateMachine,
        dry_run: bool = False,
    ):
        self.state_machine = state_machine
        self.dry_run = dry_run
        self.current_workflow: Optional[WorkflowDAG] = None
        self._lock = asyncio.Lock()
    
    async def execute_workflow(
        self,
        workflow: WorkflowDAG,
        context: DRContext,
    ) -> bool:
        """Execute a workflow DAG.
        
        Args:
            workflow: The workflow to execute
            context: DR context
            
        Returns:
            True if workflow completed successfully
        """
        async with self._lock:
            self.current_workflow = workflow
            
            try:
                while not workflow.is_complete():
                    ready_nodes = workflow.get_ready_nodes()
                    
                    if not ready_nodes:
                        if workflow.has_failures():
                            logger.error("Workflow has failures and cannot continue")
                            return False
                        # No ready nodes and no failures - we're stuck
                        await asyncio.sleep(1)
                        continue
                    
                    # Execute ready nodes in parallel
                    tasks = [
                        asyncio.create_task(self._execute_node(node, context))
                        for node in ready_nodes
                    ]
                    
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                success = not workflow.has_failures()
                
                if not success:
                    logger.error(f"Workflow {workflow.name} completed with failures")
                    await self._rollback_workflow(workflow, context)
                
                return success
                
            finally:
                self.current_workflow = None
    
    async def _execute_node(
        self,
        node: WorkflowNode,
        context: DRContext,
    ) -> None:
        """Execute a single workflow node."""
        node.status = WorkflowStatus.RUNNING
        node.start_time = datetime.now()
        
        logger.info(f"Executing node: {node.name} ({node.id})")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {node.name}")
            node.status = WorkflowStatus.COMPLETED
            node.end_time = datetime.now()
            return
        
        try:
            # Execute with timeout and retries
            for attempt in range(node.max_retries):
                try:
                    result = await asyncio.wait_for(
                        node.action(),
                        timeout=node.timeout_seconds,
                    )
                    node.result = result
                    node.status = WorkflowStatus.COMPLETED
                    node.end_time = datetime.now()
                    logger.info(f"Node {node.name} completed successfully")
                    return
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Node {node.name} timeout (attempt {attempt + 1})")
                    if attempt == node.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            logger.error(f"Node {node.name} failed: {e}")
            node.error = str(e)
            node.status = WorkflowStatus.FAILED
            node.end_time = datetime.now()
            context.error_log.append(f"{node.name}: {e}")
    
    async def _rollback_workflow(
        self,
        workflow: WorkflowDAG,
        context: DRContext,
    ) -> None:
        """Rollback a failed workflow."""
        logger.warning(f"Rolling back workflow: {workflow.name}")
        
        # Get completed nodes in reverse order
        completed_nodes = [
            node for node in workflow.nodes.values()
            if node.status == WorkflowStatus.COMPLETED
        ]
        completed_nodes.sort(key=lambda n: n.end_time or datetime.now(), reverse=True)
        
        for node in completed_nodes:
            if node.rollback_action:
                logger.info(f"Rolling back node: {node.name}")
                try:
                    await node.rollback_action()
                    node.status = WorkflowStatus.ROLLED_BACK
                except Exception as e:
                    logger.error(f"Rollback failed for {node.name}: {e}")
                    context.error_log.append(f"Rollback {node.name}: {e}")
    
    def get_current_phase(self) -> DRPhase:
        """Get current DR phase."""
        return self.current_phase
    
    def is_active(self) -> bool:
        """Check if DR is currently active."""
        return self.current_phase not in (
            DRPhase.IDLE,
            DRPhase.COMPLETED,
            DRPhase.FAILED,
        )
