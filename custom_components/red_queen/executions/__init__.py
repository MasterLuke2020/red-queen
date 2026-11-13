"""WNHF canonical and legacy execution components."""

from .engine import ExecutionPlanner
from .model import ExecutionPlan, ExecutionStep, ExecutionStatus
from .transaction import ExecutionTransaction, ExecutionTransactionStatus
from .blueprint import MultiStepBlueprint, MultiStepBlueprintStep
from .capability import (
    ConfirmationPolicy,
    EffectConfirmationMode,
    ExecutionCapability,
    ExecutionCapabilityAdapter,
)
from .locks import (
    LockDecision,
    QueueTicket,
    TransactionLock,
    TransactionLockManager,
)
from .manager import LegacyExecutionManager, ExecutionRoute
from .pipeline import ExecutionPipeline, PipelineStepResult
from .house_execution import (
    HouseExecutionResult,
    HouseExecutionState,
    HouseExecutionTransition,
    HouseRoomResult,
)
from .sequential_room import (
    SequentialRoomResult,
    SequentialRoomState,
    SequentialRoomTransition,
    SequentialStepResult,
    SequentialStepState,
)
from .real_step import (
    CommandOutcome,
    CommandStatus,
    EffectOutcome,
    EffectStatus,
    RealStepResult,
    RealStepState,
    RealStepTransition,
)
from .generic_transaction import (
    GenericTransactionResult,
    GenericTransactionState,
    GenericTransactionTransition,
)
from .simulation import (
    MultiStepSimulation,
    MultiStepSimulationStatus,
    MultiStepSimulationStep,
    MultiStepSimulationStepStatus,
)

__all__ = [
    "CanonicalActionExecutionContract",
    "REAL_EXECUTION_ENABLED_ACTIONS",
    "get_canonical_action_contract",
    "ExecutionRuntimeDiagnostics",
    "SemanticExecutionRouter",
    "SemanticRouteResult",
    "GenericPromotedExecutionPlan",
    "promote_execution_plan",
    "GenericExecutionEngine",
    "GenericRealExecutionResult",
    "GenericRealExecutionState",
    "GenericRealResultCode",
    "GenericExecutionDryRunResult",
    "GenericExecutionPlan",
    "GenericExecutionPlanner",
    "GenericExecutionRequest",
    "GenericExecutionResultCode",
    "GenericExecutionState",
    "ExecutionActionResolution",
    "SemanticExecutionManager",
    "ExecutionReadinessStatus",
    "AccessResultCatalog",
    "AccessResultCode",
    "ResultCategory",
    "ResultSeverity",
    "ConfirmationPolicy",
    "EffectConfirmationMode",
    "CommandDispatcher",
    "EffectObserver",
    "ExecutionPlan",
    "ExecutionPlanner",
    "ExecutionStatus",
    "ExecutionStep",
    "ExecutionTransaction",
    "ExecutionTransactionStatus",
    "MultiStepBlueprint",
    "MultiStepBlueprintStep",
    "ExecutionCapability",
    "ExecutionCapabilityAdapter",
    "LockDecision",
    "QueueTicket",
    "TransactionLock",
    "TransactionLockManager",
    "LegacyExecutionManager",
    "ExecutionRoute",
    "ExecutionPipeline",
    "PipelineStepResult",
    "HouseExecutionResult",
    "HouseExecutionState",
    "HouseExecutionTransition",
    "HouseRoomResult",
    "SequentialRoomResult",
    "SequentialRoomState",
    "SequentialRoomTransition",
    "SequentialStepResult",
    "SequentialStepState",
    "CommandOutcome",
    "CommandStatus",
    "EffectOutcome",
    "EffectStatus",
    "RealStepResult",
    "RealStepState",
    "RealStepTransition",
    "GenericTransactionResult",
    "GenericTransactionState",
    "GenericTransactionTransition",
    "MultiStepSimulation",
    "MultiStepSimulationStatus",
    "MultiStepSimulationStep",
    "MultiStepSimulationStepStatus",
]


from .dispatcher import CommandDispatcher
from .effect_observer import EffectObserver


from .access_codes import (
    AccessResultCatalog,
    AccessResultCode,
    ResultCategory,
    ResultSeverity,
)


from .action_contracts import (
    CanonicalActionExecutionContract,
    REAL_EXECUTION_ENABLED_ACTIONS,
    get_canonical_action_contract,
)

from .generic_manager import (
    ExecutionActionResolution,
    SemanticExecutionManager,
    ExecutionReadinessStatus,
)


from .generic_contract import (
    GenericExecutionDryRunResult,
    GenericExecutionPlan,
    GenericExecutionRequest,
    GenericExecutionResultCode,
    GenericExecutionState,
    GenericPromotedExecutionPlan,
    promote_execution_plan,
)
from .generic_planner import GenericExecutionPlanner


from .generic_real import (
    GenericExecutionEngine,
    GenericRealExecutionResult,
    GenericRealExecutionState,
    GenericRealResultCode,
)


from .semantic_router import (
    SemanticExecutionRouter,
    SemanticRouteResult,
)

from .runtime_diagnostics import ExecutionRuntimeDiagnostics
