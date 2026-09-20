from app import create_app, db
from app.models import Product, User

def make_app(tmp_path):
    return create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/test.db", "SECRET_KEY": "test"})

def test_catalog_and_cart(tmp_path):
    app = make_app(tmp_path)
    client = app.test_client()
    assert client.get("/").status_code == 200
    product = Product.query.first() if False else None
    with app.app_context(): product_id = Product.query.first().id
    response = client.post(f"/cart/add/{product_id}", data={"quantity": 2}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Order summary" in client.get("/cart").data

def test_register_login_and_protected_checkout(tmp_path):
    app = make_app(tmp_path); client = app.test_client()
    response = client.post("/register", data={"name":"Avery Lane","email":"avery@example.com","password":"a-long-safe-password","confirm":"a-long-safe-password"}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context(): assert User.query.filter_by(email="avery@example.com").first()
    client.post("/logout")
    assert client.get("/account/orders").status_code == 302
