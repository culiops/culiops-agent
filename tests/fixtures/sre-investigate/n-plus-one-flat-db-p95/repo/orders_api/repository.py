"""Data access for orders (state at tag v2.15.0)."""

ORDERS_SQL = """
SELECT id, customer_id, status, total_minor, currency, created_at, shipment_eta
FROM orders
WHERE customer_id = %(customer_id)s
ORDER BY created_at DESC
LIMIT %(limit)s
"""

ORDERS_WITH_ITEMS_SQL = """
SELECT o.id, o.customer_id, o.status, o.total_minor, o.currency, o.created_at, o.shipment_eta,
       i.id AS item_id, i.sku, i.quantity, i.status AS item_status
FROM (
    SELECT * FROM orders WHERE customer_id = %(customer_id)s
    ORDER BY created_at DESC LIMIT %(limit)s
) o
LEFT JOIN order_items i ON i.order_id = o.id
ORDER BY o.created_at DESC
"""

ITEMS_SQL = """
SELECT id, order_id, sku, quantity, status
FROM order_items
WHERE order_id = %(order_id)s
"""


class OrdersRepository:
    def __init__(self, pool):
        self.pool = pool

    def list_orders(self, customer_id, limit):
        with self.pool.connection() as conn:
            rows = conn.execute(ORDERS_SQL, {"customer_id": customer_id, "limit": limit}).fetchall()
        return [Order.from_row(r) for r in rows]

    def list_orders_with_items(self, customer_id, limit):
        """One round trip: orders plus their items (used by the list handler up to v2.14.0)."""
        with self.pool.connection() as conn:
            rows = conn.execute(ORDERS_WITH_ITEMS_SQL, {"customer_id": customer_id, "limit": limit}).fetchall()
        return Order.group_rows(rows)

    def list_items(self, order_id):
        with self.pool.connection() as conn:
            rows = conn.execute(ITEMS_SQL, {"order_id": order_id}).fetchall()
        return [Item.from_row(r) for r in rows]


from orders_api.models import Item, Order  # noqa: E402  (import cycle with models)
