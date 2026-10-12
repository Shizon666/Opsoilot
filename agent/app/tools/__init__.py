"""Agent tools: V1 whitelist via Business Client (+ Phase 10 knowledge).

Permission tools remain in the package as Legacy; they are not bound to the graph.
"""

from app.tools.knowledge import KNOWLEDGE_TOOLS, search_knowledge
from app.tools.permission import PERMISSION_TOOLS, create_permission, get_my_permissions
from app.tools.service import SERVICE_TOOLS, get_service_status, list_services
from app.tools.ticket import TICKET_TOOLS, create_ticket, get_ticket, search_tickets, update_ticket
from app.tools.user import USER_TOOLS, get_current_user

# Historical Phase 8 set (includes Legacy Permission). Not used at runtime.
PHASE8_TOOLS = [*USER_TOOLS, *PERMISSION_TOOLS]

# V1 runtime whitelist (Phase C-1). search_knowledge uses local cosine RAG (Phase C-2).
AGENT_TOOLS = [
    *USER_TOOLS,
    *SERVICE_TOOLS,
    *TICKET_TOOLS,
    *KNOWLEDGE_TOOLS,
]

__all__ = [
    "PHASE8_TOOLS",
    "AGENT_TOOLS",
    "USER_TOOLS",
    "SERVICE_TOOLS",
    "TICKET_TOOLS",
    "PERMISSION_TOOLS",
    "KNOWLEDGE_TOOLS",
    "get_current_user",
    "list_services",
    "get_service_status",
    "search_tickets",
    "get_ticket",
    "create_ticket",
    "update_ticket",
    "get_my_permissions",
    "create_permission",
    "search_knowledge",
]
