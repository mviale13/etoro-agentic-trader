from enum import StrEnum


class EventType(StrEnum):
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_OUTCOME_RECORDED = "recommendation_outcome_recorded"
    PORTFOLIO_ANALYZED = "portfolio_analyzed"
    ORDER_PROPOSED = "order_proposed"
    ORDER_APPROVED = "order_approved"
    ORDER_EXECUTED = "order_executed"
    POSITION_CLOSED = "position_closed"
    MEMORY_RECORDED = "memory_recorded"
    EXECUTIVE_DECISION_RECORDED = "executive_decision_recorded"
