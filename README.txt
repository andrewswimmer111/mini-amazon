Browsing (guest)
- app/index.py
- app/models/product.py
- app/item.py
- templates: app/templates/index.html, app/templates/_products_fragment.html, app/templates/product_detail.html

Guest restrictions (login required)
- app/cart.py
- app/item.py
- app/sellers.py

Authentication & profile
- app/users.py
- app/models/user.py

Buyer features (cart, checkout, history)
- app/cart.py
- app/models/cart.py
- app/models/purchase.py

Seller features (inventory, orders)
- app/sellers.py
- app/models/inventory.py

Security, validation, DB
- app/db.py
- app/__init__.py
- WTForms validators: app/users.py, app/item.py, app/sellers.py

Templates & static
- app/templates/*.html (register.html, login.html, cart.html, userprofile.html, seller_inventory.html, seller_orders.html, create_product.html, update_profile.html)
- app/static/css/*, app/static/product_images/

Notes
- Login protection uses @login_required in routes across app/cart.py, app/item.py, app/sellers.py, etc.
- SQL queries use parameter binding via app/db.py (DB.execute) to mitigate SQL injection.
