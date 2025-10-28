from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

# База пользователей
users = {
    "admin@stolovaya.kg": {"name": "Главный админ", "password": "admin123", "role": "Administrator"}
}

# Пример заказов
orders_list = [
    {"id": 1, "dish": "Пицца Маргарита", "status": "Активен"},
    {"id": 2, "dish": "Суши сет Самурай", "status": "Активен"},
    {"id": 3, "dish": "Бургер Чеддер", "status": "Доставлен"},
]

# Меню блюд с категориями (в сомах)
menu_items_list = [
    {"id": 1, "name": "Пицца Маргарита", "price": 450, "category": "Пицца", "image": "🍕", "description": "Классическая пицца с томатным соусом и моцареллой"},
    {"id": 2, "name": "Суши сет Самурай", "price": 1200, "category": "Суши", "image": "🍣", "description": "Ассорти из свежих суши и роллов"},
    {"id": 3, "name": "Бургер Чеддер", "price": 350, "category": "Бургеры", "image": "🍔", "description": "Сочный бургер с сыром чеддер и овощами"},
    {"id": 4, "name": "Паста Карбонара", "price": 420, "category": "Паста", "image": "🍝", "description": "Итальянская паста с беконом и соусом"},
    {"id": 5, "name": "Салат Цезарь", "price": 280, "category": "Салаты", "image": "🥗", "description": "Классический салат с курицей и соусом цезарь"},
    {"id": 6, "name": "Кола", "price": 120, "category": "Напитки", "image": "🥤", "description": "Освежающий газированный напиток"},
]

# Избранное пользователей
favorites = {}

# Корзины пользователей
carts = {}

def get_next_id():
    return max([item['id'] for item in menu_items_list], default=0) + 1

def get_categories():
    return list(set(item['category'] for item in menu_items_list))

# --- ГЛАВНАЯ СТРАНИЦА ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")

        if action == "register":
            if email in users:
                flash("Пользователь уже существует!", "error")
            else:
                users[email] = {"name": name, "password": password, "role": "Customer"}
                flash("Регистрация прошла успешно! Теперь войдите.", "success")
                return redirect(url_for("index"))

        elif action == "login":
            if email in users and users[email]["password"] == password:
                session["user"] = email
                flash("Вход выполнен!", "success")

                user_role = users[email]["role"]
                if user_role == "Administrator":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("dashboard"))
            else:
                flash("Неверный email или пароль!", "error")

    return render_template("index.html")

# --- ЛИЧНЫЙ КАБИНЕТ ---
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    email = session["user"]
    user = users[email]
    
    # Получаем избранное пользователя
    user_favorites = favorites.get(email, [])
    favorite_items = [item for item in menu_items_list if item["id"] in user_favorites]
    
    # Получаем корзину пользователя
    user_cart = carts.get(email, {})
    cart_items = []
    total_price = 0
    
    for item_id, quantity in user_cart.items():
        for item in menu_items_list:
            if item["id"] == item_id:
                cart_item = item.copy()
                cart_item["quantity"] = quantity
                cart_item["total"] = item["price"] * quantity
                cart_items.append(cart_item)
                total_price += cart_item["total"]
                break
    
    menu_items = [
        ("Меню блюд", "menu"),
        ("Корзина", "cart"),
        ("Мои заказы", "orders_page"),
        ("История заказов", "history"),
        ("Выход", "logout")
    ]

    return render_template("dashboard.html", 
                         name=user["name"], 
                         role=user["role"], 
                         menu_items=menu_items,
                         favorite_items=favorite_items,
                         cart_items=cart_items,
                         total_price=total_price)

# --- АДМИН-ПАНЕЛЬ ---
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    user = users[session["user"]]
    if user["role"] != "Administrator":
        return redirect(url_for("dashboard"))

    return render_template("admin_dashboard.html", name=user["name"], 
                         menu_items_list=menu_items_list, 
                         orders_list=orders_list, 
                         users=users)

# --- МЕНЮ БЛЮД С ФИЛЬТРАЦИЕЙ И ПОИСКОМ ---
@app.route("/menu")
def menu():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    # Фильтрация блюд
    filtered_items = menu_items_list
    
    if category:
        filtered_items = [item for item in filtered_items if item['category'] == category]
    
    if search:
        search_lower = search.lower()
        filtered_items = [item for item in filtered_items if search_lower in item['name'].lower() or search_lower in item['description'].lower()]
    
    # Получаем избранное пользователя
    user_favorites = favorites.get(session["user"], [])
    
    categories = get_categories()
    
    return render_template("menu.html", 
                         menu_items=filtered_items,
                         categories=categories,
                         selected_category=category,
                         search_query=search,
                         user_favorites=user_favorites)

# --- ДОБАВЛЕНИЕ/УДАЛЕНИЕ ИЗ ИЗБРАННОГО ---
@app.route("/toggle_favorite/<int:item_id>")
def toggle_favorite(item_id):
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))
    
    user_email = session["user"]
    
    if user_email not in favorites:
        favorites[user_email] = []
    
    if item_id in favorites[user_email]:
        favorites[user_email].remove(item_id)
        flash("Блюдо удалено из избранного", "info")
    else:
        favorites[user_email].append(item_id)
        flash("Блюдо добавлено в избранное!", "success")
    
    return redirect(request.referrer or url_for('menu'))

# --- КОРЗИНА ---
@app.route("/cart")
def cart():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))
    
    user_email = session["user"]
    user_cart = carts.get(user_email, {})
    
    cart_items = []
    total_price = 0
    
    for item_id, quantity in user_cart.items():
        for item in menu_items_list:
            if item["id"] == item_id:
                cart_item = item.copy()
                cart_item["quantity"] = quantity
                cart_item["total"] = item["price"] * quantity
                cart_items.append(cart_item)
                total_price += cart_item["total"]
                break
    
    return render_template("cart.html", 
                         cart_items=cart_items, 
                         total_price=total_price)

# --- ДОБАВЛЕНИЕ В КОРЗИНУ ---
@app.route("/add_to_cart/<int:item_id>", methods=["GET", "POST"])
def add_to_cart(item_id):
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))
    
    user_email = session["user"]
    
    if user_email not in carts:
        carts[user_email] = {}
    
    if item_id in carts[user_email]:
        carts[user_email][item_id] += 1
    else:
        carts[user_email][item_id] = 1
    
    # Находим название блюда для сообщения
    item_name = next((item["name"] for item in menu_items_list if item["id"] == item_id), "Блюдо")
    flash(f"'{item_name}' добавлено в корзину!", "success")
    
    return redirect(request.referrer or url_for('menu'))

# --- УДАЛЕНИЕ ИЗ КОРЗИНЫ ---
@app.route("/remove_from_cart/<int:item_id>")
def remove_from_cart(item_id):
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))
    
    user_email = session["user"]
    
    if user_email in carts and item_id in carts[user_email]:
        del carts[user_email][item_id]
        flash("Блюдо удалено из корзины", "info")
    
    return redirect(url_for('cart'))

# --- ОБНОВЛЕНИЕ КОЛИЧЕСТВА В КОРЗИНЕ ---
@app.route("/update_cart/<int:item_id>", methods=["POST"])
def update_cart(item_id):
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))
    
    user_email = session["user"]
    quantity = request.form.get("quantity", type=int)
    
    if user_email in carts and item_id in carts[user_email]:
        if quantity > 0:
            carts[user_email][item_id] = quantity
        else:
            del carts[user_email][item_id]
    
    return redirect(url_for('cart'))

# --- ОФОРМЛЕНИЕ ЗАКАЗА ---
@app.route("/checkout")
def checkout():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))
    
    user_email = session["user"]
    
    if user_email not in carts or not carts[user_email]:
        flash("Корзина пуста!", "error")
        return redirect(url_for('cart'))
    
    # Здесь можно добавить логику оформления заказа
    # Пока просто очищаем корзину
    carts[user_email] = {}
    
    flash("Заказ успешно оформлен! Ожидайте доставку.", "success")
    return redirect(url_for('dashboard'))

# --- УПРАВЛЕНИЕ МЕНЮ ---
@app.route("/manage_menu", methods=["GET", "POST"])
def manage_menu():
    if "user" not in session or users[session["user"]]["role"] != "Administrator":
        flash("⛔ Доступ запрещён!", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        action = request.form.get("action")
        item_id = request.form.get("id")
        name = request.form.get("name")
        price = request.form.get("price")
        category = request.form.get("category")
        description = request.form.get("description")

        if action == "add":
            new_item = {
                "id": get_next_id(), 
                "name": name, 
                "price": float(price),
                "category": category,
                "image": "🍽️",
                "description": description
            }
            menu_items_list.append(new_item)
            flash(f"Блюдо '{name}' добавлено!", "success")
        elif action == "edit":
            for item in menu_items_list:
                if str(item["id"]) == item_id:
                    item["name"] = name
                    item["price"] = float(price)
                    item["category"] = category
                    item["description"] = description
                    flash(f"Блюдо '{name}' обновлено!", "success")
        elif action == "delete":
            menu_items_list[:] = [item for item in menu_items_list if str(item["id"]) != item_id]
            flash("Блюдо удалено!", "info")

    categories = get_categories()
    return render_template("manage_menu.html", menu_items=menu_items_list, categories=categories)

# --- ОСТАЛЬНЫЕ СТРАНИЦЫ ---
@app.route("/orders")
def orders_page():
    if "user" not in session:
        return redirect(url_for("index"))

    active_orders = [o for o in orders_list if o["status"] == "Активен"]
    completed_orders = [o for o in orders_list if o["status"] != "Активен"]

    return render_template("orders.html", active_orders=active_orders, completed_orders=completed_orders)

@app.route("/history")
def history():
    return "<h2>📜 История заказов</h2><a href='/dashboard'>Назад</a>"

@app.route("/analytics")
def analytics():
    if "user" not in session or users[session["user"]]["role"] != "Administrator":
        flash("⛔ Доступ запрещён!", "error")
        return redirect(url_for("dashboard"))
    return "<h2>📊 Аналитика блюд</h2><a href='/admin_dashboard'>Назад</a>"

# --- ВЫХОД ---
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    print("🚀 ИС Столовая КГТУ запущена!")
    print("📍 Адрес: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)