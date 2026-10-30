"""GET /orders: list a customer's recent orders (state at tag v2.15.0)."""

from orders_api.repository import OrdersRepository
from orders_api.serializers import serialize_order


def list_orders(request, repo: OrdersRepository):
    """Return up to `limit` orders for the authenticated customer, newest first.

    Each order carries its line items so the list view can show per-item status.
    """
    customer_id = request.auth.customer_id
    limit = min(int(request.query.get("limit", 50)), 50)

    orders = repo.list_orders(customer_id, limit=limit)
    # items are loaded separately so the list view can show per-item status
    for order in orders:
        order.items = repo.list_items(order.id)

    return {
        "orders": [serialize_order(o, include_items=True) for o in orders],
        "next": orders[-1].id if len(orders) == limit else None,
    }
