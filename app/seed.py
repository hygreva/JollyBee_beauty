from . import db
from .models import Product

PRODUCTS = [
    ("dew-drop-serum", "Dew Drop Serum", "Skincare", "A silky niacinamide and hyaluronic acid serum for bouncy, luminous skin.", "Niacinamide 5%, Hyaluronic Acid, Panthenol", 3800, "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=1000&q=85", True),
    ("cloud-cream", "Cloud Cream", "Skincare", "A cushiony ceramide moisturizer that comforts dry and sensitive skin without heaviness.", "Ceramides, Squalane, Oat Kernel", 4200, "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=1000&q=85", True),
    ("petal-flush", "Petal Flush", "Makeup", "A blendable cream blush with a soft satin finish and buildable rose color.", "Jojoba Oil, Vitamin E, Mineral Pigments", 2800, "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=1000&q=85", True),
    ("velvet-lip-oil", "Velvet Lip Oil", "Makeup", "A plush, non-sticky lip oil that cushions lips in sheer berry color.", "Meadowfoam Seed Oil, Squalane, Vitamin E", 2400, "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=1000&q=85", False),
    ("sun-veil-spf", "Sun Veil SPF 40", "Skincare", "Invisible broad-spectrum protection with a comfortable natural finish and no white cast.", "Zinc Oxide, Bisabolol, Green Tea", 3600, "https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8?auto=format&fit=crop&w=1000&q=85", True),
    ("moon-bloom-mist", "Moon Bloom Mist", "Fragrance", "A delicate skin and hair mist with jasmine, pear, and warm sandalwood.", "Alcohol Denat., Fragrance, Glycerin", 3200, "https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=1000&q=85", False),
    ("silk-reset-mask", "Silk Reset Mask", "Haircare", "A weekly conditioning treatment for softer, shinier, more manageable lengths.", "Rice Protein, Argan Oil, Shea Butter", 3400, "https://images.unsplash.com/photo-1522338242992-e1a54906a8da?auto=format&fit=crop&w=1000&q=85", False),
    ("soft-focus-powder", "Soft Focus Powder", "Makeup", "A translucent finishing powder that blurs shine while keeping skin fresh.", "Silica, Rice Powder, Vitamin E", 3000, "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=1000&q=85", False),
]

def seed_products():
    if Product.query.first(): return
    for slug, name, category, desc, ingredients, price, image, featured in PRODUCTS:
        db.session.add(Product(slug=slug, name=name, category=category, description=desc, ingredients=ingredients, price_cents=price, image_url=image, featured=featured))
    db.session.commit()
