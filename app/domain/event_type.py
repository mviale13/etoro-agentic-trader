from enum import StrEnum


class EventType(StrEnum):
    RECOMMENDATION_GENERATED = "recommendation_generated"
    PORTFOLIO_ANALYZED = "portfolio_analyzed"
    ORDER_PROPOSED = "order_proposed"
    ORDER_APPROVED = "order_approved"
    ORDER_EXECUTED = "order_executed"
    POSITION_CLOSED = "position_closed"
