from fnb.services.payment_service import PaymentService


class PaymentController:
    def __init__(self, payment_service: PaymentService) -> None:
        self._payment_service = payment_service

    def list_unpaid_orders(self) -> list[dict]:
        return [order.to_dict() for order in self._payment_service.list_unpaid_orders()]

    def preview_bill(self, order_id: str) -> dict:
        return self._payment_service.preview_bill(order_id)

    def checkout(self, order_id: str) -> dict:
        return self._payment_service.checkout(order_id).to_dict()
