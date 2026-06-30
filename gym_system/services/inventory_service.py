from database.models.inventory import Product, StockMovement
from database.db import db

class InventoryService:
    @staticmethod
    def build_movement(product_id, quantity, reason='Venta'):
        """Crea un StockMovement sin hacer commit — para usarlo dentro de una transacción mayor."""
        return StockMovement(
            product_id=product_id,
            movement_type='salida',
            quantity=quantity,
            reason=reason
        )

    @staticmethod
    def add_stock(product_id, quantity, reason='Entrada'):
        product = Product.query.get_or_404(product_id)
        product.quantity += quantity
        mov = StockMovement(product_id=product_id, movement_type='entrada', quantity=quantity, reason=reason)
        db.session.add(mov)
        db.session.commit()

    @staticmethod
    def remove_stock(product_id, quantity, reason='Venta'):
        product = Product.query.get_or_404(product_id)
        if product.quantity < quantity:
            raise ValueError('Stock insuficiente.')
        product.quantity -= quantity
        mov = StockMovement(product_id=product_id, movement_type='salida', quantity=quantity, reason=reason)
        db.session.add(mov)
        db.session.commit()

    @staticmethod
    def low_stock():
        return Product.query.filter(Product.quantity <= Product.min_stock, Product.is_active == True).all()
