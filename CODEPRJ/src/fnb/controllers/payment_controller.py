from fnb.services.payment_service import PaymentService


class PaymentController:
    def __init__(self, payment_service: PaymentService) -> None:
        self._payment_service = payment_service

    def preview_bill(self, order_id: str, discount_amount: int | None = None) -> dict:
        return self._payment_service.preview_bill(order_id, discount_amount)

    def checkout(
        self,
        order_id: str,
        payment_method: str = "CASH",
        discount_amount: int = 0,
    ) -> dict:
        return self._payment_service.checkout(
            order_id, payment_method=payment_method, discount_amount=discount_amount
        ).to_dict()
