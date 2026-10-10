from fnb.services.payment_service import PaymentService


class PaymentController:
    def __init__(self, payment_service: PaymentService) -> None:
        self._payment_service = payment_service

    def checkout(self, order_id: str) -> dict:
        return self._payment_service.checkout(order_id).to_dict()
