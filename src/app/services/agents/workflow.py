import logging
from collections.abc import Callable
from time import perf_counter
from typing import Any

from langgraph.graph import END, StateGraph

from app.services.agents.nodes import WorkflowNodes, build_nodes
from app.services.agents.state import AgentState, WorkflowState

WORKFLOW_ORDER = (
    "parsing",
    "extraction",
    "semantic_matching",
    "retrieval",
    "recommendation_generation",
    "optional_bullet_rewriting",
)

logger = logging.getLogger(__name__)


class ResumeVacancyWorkflow:
    def __init__(self, nodes: WorkflowNodes | None = None) -> None:
        self._graph = _compile_graph(build_nodes(nodes))

    def run(self, state: WorkflowState) -> WorkflowState:
        result = self._graph.invoke(state.model_dump(mode="python"))
        return WorkflowState.model_validate(result)


def run_workflow(
    resume_text: str,
    vacancy_text: str,
    enable_bullet_rewriting: bool = False,
    nodes: WorkflowNodes | None = None,
) -> WorkflowState:
    return ResumeVacancyWorkflow(nodes=nodes).run(
        WorkflowState(
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            enable_bullet_rewriting=enable_bullet_rewriting,
        )
    )


def _compile_graph(node_mapping: dict[str, Callable[[Any], dict[str, Any]]]) -> Any:
    graph = StateGraph(WorkflowState)
    for node_name in WORKFLOW_ORDER:
        graph.add_node(node_name, _timed_node(node_name, node_mapping[node_name]))

    graph.set_entry_point(WORKFLOW_ORDER[0])
    for source, target in zip(WORKFLOW_ORDER[:-1], WORKFLOW_ORDER[1:], strict=True):
        graph.add_edge(source, target)
    graph.add_edge(WORKFLOW_ORDER[-1], END)
    return graph.compile()


def _timed_node(
    node_name: str,
    node: Callable[[Any], dict[str, Any]],
) -> Callable[[Any], dict[str, Any]]:
    def wrapped(state: Any) -> dict[str, Any]:
        start_time = perf_counter()
        result = node(state)
        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        result_state = WorkflowState.model_validate(result)
        result_state.workflow_timings_ms = {
            **result_state.workflow_timings_ms,
            node_name: duration_ms,
        }
        logger.info(
            "workflow_step_completed",
            extra={
                "workflow_step": node_name,
                "duration_ms": duration_ms,
            },
        )
        return result_state.model_dump(mode="python")

    return wrapped


__all__ = ["AgentState", "ResumeVacancyWorkflow", "WORKFLOW_ORDER", "WorkflowState", "run_workflow"]
