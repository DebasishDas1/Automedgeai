import structlog
import threading
from workflows.hvac.graph import build_hvac_chat_graph, build_hvac_post_chat_graph
from workflows.pest_control.graph import build_pest_chat_graph, build_pest_post_chat_graph
from workflows.plumbing.graph import build_plumbing_chat_graph, build_plumbing_post_chat_graph
from workflows.roofing.graph import build_roofing_chat_graph, build_roofing_post_chat_graph

logger = structlog.get_logger(__name__)

class WorkflowRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WorkflowRegistry, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        logger.info("compiling_graphs")
        self._chat_graphs = {
            "hvac": build_hvac_chat_graph(),
            "pest_control": build_pest_chat_graph(),
            "plumbing": build_plumbing_chat_graph(),
            "roofing": build_roofing_chat_graph(),
        }
        self._post_graphs = {
            "hvac": build_hvac_post_chat_graph(),
            "pest_control": build_pest_post_chat_graph(),
            "plumbing": build_plumbing_post_chat_graph(),
            "roofing": build_roofing_post_chat_graph(),
        }

    def get_chat_graph(self, vertical: str):
        return self._chat_graphs.get(vertical)

    def get_post_graph(self, vertical: str):
        return self._post_graphs.get(vertical)

registry = WorkflowRegistry()
