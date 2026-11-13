"""Models for the intentionally imperfect order-management application."""
from dataclasses import dataclass


@dataclass
class Product:
    sku: str
    name: str
    price: float
    stock: int


@dataclass
class CartLine:
    sku: str
    name: str
    unit_price: float
    quantity: int


@dataclass
class OrderResult:
    order_id: int | None
    status: str
    total: float
