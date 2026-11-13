
import pytest

from cart import ShoppingCart
from repository import StoreRepository
from setup_db import initialize


@pytest.fixture
def cart_and_repo(tmp_path):
    db_path = tmp_path / 'test_shop.db'
    initialize(str(db_path))
    repo = StoreRepository(str(db_path))
    return ShoppingCart('student', repo), repo


# Defect 1: Invalid add quantities

def test_add_valid_quantity(cart_and_repo):
    cart, _ = cart_and_repo
    assert cart.add_item('USB-01', 2) is True
    assert cart.lines[0].quantity == 2


def test_reject_zero_quantity(cart_and_repo):
    cart, _ = cart_and_repo
    assert cart.add_item('USB-01', 0) is False
    assert cart.lines == []


def test_reject_negative_and_noninteger_quantities(cart_and_repo):
    cart, _ = cart_and_repo
    for quantity in (-2, 1.5, '2', True):
        assert cart.add_item('USB-01', quantity) is False
    assert cart.lines == []


# Defect 2: Duplicate products exceeding stock

def test_duplicate_product_combines_quantities(cart_and_repo):
    cart, _ = cart_and_repo
    assert cart.add_item('LAP-01', 2) is True
    assert cart.add_item('LAP-01', 3) is True
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 5


def test_duplicate_product_cannot_exceed_stock(cart_and_repo):
    cart, _ = cart_and_repo
    assert cart.add_item('LAP-01', 4) is True
    assert cart.add_item('LAP-01', 2) is False
    assert cart.lines[0].quantity == 4


# Defect 3: Invalid removal quantities

def test_remove_partial_quantity(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 5)
    assert cart.remove_item('USB-01', 2) is True
    assert cart.lines[0].quantity == 3


def test_reject_invalid_removal_quantity(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 5)
    for quantity in (0, -2, 1.5, '2', True):
        assert cart.remove_item('USB-01', quantity) is False
    assert cart.lines[0].quantity == 5


# Defect 4: Discount recalculation after cart changes

def test_discount_recalculates_after_adding(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 2)
    assert cart.apply_discount('WELCOME10') is True
    cart.add_item('USB-01', 1)
    assert cart.total() == pytest.approx(3 * 9.99 * 0.9)


def test_discount_recalculates_after_removing(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 3)
    cart.apply_discount('WELCOME10')
    assert cart.remove_item('USB-01', 1) is True
    assert cart.total() == pytest.approx(2 * 9.99 * 0.9)


# Defect 5: Discount stacking

def test_second_discount_does_not_stack(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 10)
    cart.apply_discount('WELCOME10')
    cart.apply_discount('STUDENT20')
    assert cart.total() == pytest.approx(cart.subtotal() * 0.8)


# Defect 6: Negative discounted totals

def test_fixed_discount_cannot_make_total_negative(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 1)
    assert cart.apply_discount('SAVE15') is True
    assert cart.total() == 0


# Defect 7: Repeated cart loading

def test_repeated_load_does_not_duplicate_items(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 3)
    cart.save()
    cart.load()
    cart.load()
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 3


def test_load_replaces_existing_cart(cart_and_repo):
    cart, _ = cart_and_repo
    cart.add_item('USB-01', 2)
    cart.save()
    cart.add_item('MOU-01', 1)
    cart.load()
    assert [(line.sku, line.quantity) for line in cart.lines] == [('USB-01', 2)]


# Defect 8: SQL injection 

def test_product_lookup_rejects_sql_injection(cart_and_repo):
    _, repo = cart_and_repo
    assert repo.get_product("USB-01' OR '1'='1") is None
    assert repo.get_product('USB-01').sku == 'USB-01'


def test_saved_cart_lookup_rejects_sql_injection(cart_and_repo):
    cart, repo = cart_and_repo
    cart.add_item('USB-01', 2)
    cart.save()
    assert repo.get_saved_cart("student' OR '1'='1") == []
    assert repo.get_saved_cart('student') == [('USB-01', 2)]

