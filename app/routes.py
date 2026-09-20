import stripe
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from . import csrf, db
from .forms import LoginForm, RegisterForm
from .models import Order, OrderItem, Product, User

bp = Blueprint("shop", __name__)

def cart_data():
    cart = session.get("cart", {})
    products = Product.query.filter(Product.id.in_([int(k) for k in cart.keys()])).all() if cart else []
    lines = [{"product": p, "quantity": int(cart[str(p.id)]), "subtotal": p.price_cents * int(cart[str(p.id)])} for p in products]
    return lines, sum(x["subtotal"] for x in lines)

@bp.app_context_processor
def globals():
    return {"cart_count": sum(session.get("cart", {}).values()), "money": lambda cents: f"${cents / 100:,.2f}"}

@bp.get("/")
def home():
    return render_template("home.html", featured=Product.query.filter_by(featured=True).all())

@bp.get("/shop")
def shop():
    query = Product.query
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    if q: query = query.filter(or_(Product.name.ilike(f"%{q}%"), Product.description.ilike(f"%{q}%")))
    if category: query = query.filter_by(category=category)
    return render_template("shop.html", products=query.order_by(Product.name).all(), q=q, category=category, categories=[r[0] for r in db.session.query(Product.category).distinct()])

@bp.get("/product/<slug>")
def product(slug):
    return render_template("product.html", product=Product.query.filter_by(slug=slug).first_or_404())

@bp.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = db.get_or_404(Product, product_id)
    qty = max(1, min(int(request.form.get("quantity", 1)), product.inventory, 10))
    cart = session.get("cart", {})
    cart[str(product.id)] = min(cart.get(str(product.id), 0) + qty, product.inventory, 10)
    session["cart"] = cart
    flash(f"{product.name} added to your bag.", "success")
    return redirect(request.referrer or url_for("shop.shop"))

@bp.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        cart = session.get("cart", {})
        for key in list(cart):
            product = db.session.get(Product, int(key))
            qty = max(0, min(int(request.form.get(f"qty_{key}", cart[key])), product.inventory if product else 0, 10))
            if qty: cart[key] = qty
            else: cart.pop(key, None)
        session["cart"] = cart
        flash("Your bag has been updated.", "success")
        return redirect(url_for("shop.cart"))
    lines, total = cart_data()
    return render_template("cart.html", lines=lines, total=total)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated: return redirect(url_for("shop.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if User.query.filter_by(email=email).first():
            flash("An account already exists for that email.", "error")
        else:
            user = User(name=form.name.data.strip(), email=email); user.set_password(form.password.data)
            db.session.add(user); db.session.commit(); login_user(user)
            return redirect(url_for("shop.shop"))
    return render_template("auth.html", form=form, title="Create your account", mode="register")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated: return redirect(url_for("shop.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user); return redirect(url_for("shop.cart"))
        flash("Invalid email or password.", "error")
    return render_template("auth.html", form=form, title="Welcome back", mode="login")

@bp.post("/logout")
@login_required
def logout():
    logout_user(); return redirect(url_for("shop.home"))

@bp.post("/checkout")
@login_required
def checkout():
    lines, total = cart_data()
    if not lines: return redirect(url_for("shop.cart"))
    if not current_app.config["STRIPE_SECRET_KEY"]:
        flash("Stripe test keys are not configured yet. Add them to .env to enable checkout.", "error")
        return redirect(url_for("shop.cart"))
    for line in lines:
        if line["quantity"] > line["product"].inventory:
            flash(f"Only {line['product'].inventory} units of {line['product'].name} remain.", "error")
            return redirect(url_for("shop.cart"))
    order = Order(user_id=current_user.id, total_cents=total)
    for line in lines:
        order.items.append(OrderItem(product_id=line["product"].id, product_name=line["product"].name, quantity=line["quantity"], unit_price_cents=line["product"].price_cents))
    db.session.add(order); db.session.commit()
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    checkout_session = stripe.checkout.Session.create(
        mode="payment", customer_email=current_user.email,
        line_items=[{"price_data": {"currency": current_app.config["STRIPE_CURRENCY"], "product_data": {"name": x["product"].name}, "unit_amount": x["product"].price_cents}, "quantity": x["quantity"]} for x in lines],
        shipping_address_collection={"allowed_countries": ["US", "CA"]},
        success_url=url_for("shop.success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=url_for("shop.cart", _external=True), metadata={"order_id": str(order.id)},
    )
    order.stripe_session_id = checkout_session.id; db.session.commit()
    return redirect(checkout_session.url, code=303)

@bp.get("/checkout/success")
@login_required
def success():
    order = Order.query.filter_by(stripe_session_id=request.args.get("session_id"), user_id=current_user.id).first_or_404()
    if order.status == "paid": session["cart"] = {}
    return render_template("success.html", order=order)

@bp.post("/stripe/webhook")
@csrf.exempt
def stripe_webhook():
    secret = current_app.config["STRIPE_WEBHOOK_SECRET"]
    if not secret: return jsonify(error="Webhook secret not configured"), 503
    try:
        event = stripe.Webhook.construct_event(request.data, request.headers.get("Stripe-Signature"), secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify(error="Invalid webhook"), 400
    if event["type"] == "checkout.session.completed":
        obj = event["data"]["object"]
        order = Order.query.filter_by(stripe_session_id=obj["id"]).first()
        if order and order.status != "paid":
            order.status = "paid"
            details = obj.get("shipping_details") or {}
            order.shipping_name = details.get("name")
            order.shipping_address = str(details.get("address") or "")
            for item in order.items: item.product.inventory = max(0, item.product.inventory - item.quantity)
            db.session.commit()
    return jsonify(received=True)

@bp.get("/account/orders")
@login_required
def orders():
    return render_template("orders.html", orders=Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all())
