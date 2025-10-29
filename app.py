from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import current_user

# --- Инициализация Flask ---
app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- База пользователей ---
users = {
    "admin@stolovaya.kg": {
        "name": "Главный админ",
        "password": "admin123",
        "role": "Administrator"
    },
    "customer@gmail.com": {
        "name": "Покупатель",
        "password": "123",
        "role": "Customer"
    }
}

# --- Пример заказов ---
orders_list = [
    {"id": 1, "dish": "Пицца Маргарита", "status": "Активен"},
    {"id": 2, "dish": "Суши сет Самурай", "status": "Активен"},
    {"id": 3, "dish": "Бургер Чеддер", "status": "Доставлен"},
]

# --- Меню блюд с категориями (в сомах) ---
menu_items_list = [
    {"id": 1, "name": "Пицца Маргарита", "price": 450, "category": "Пицца", "image": "🍕", "description": "Классическая пицца с томатным соусом и моцареллой"},
    {"id": 2, "name": "Суши сет Самурай", "price": 1200, "category": "Суши", "image": "🍣", "description": "Ассорти из свежих суши и роллов"},
    {"id": 3, "name": "Бургер Чеддер", "price": 350, "category": "Бургеры", "image": "🍔", "description": "Сочный бургер с сыром чеддер и овощами"},
    {"id": 4, "name": "Паста Карбонара", "price": 420, "category": "Паста", "image": "🍝", "description": "Итальянская паста с беконом и соусом"},
    {"id": 5, "name": "Салат Цезарь", "price": 280, "category": "Салаты", "image": "🥗", "description": "Классический салат с курицей и соусом цезарь"},
    {"id": 6, "name": "Кола", "price": 120, "category": "Напитки", "image": "🥤", "description": "Освежающий газированный напиток"},
]

# --- Хранилища данных ---
favorites = {}      # Избранное пользователей
carts = {}          # Корзины пользователей
active_orders = []  # Активные заказы
completed_orders = []  # Завершённые заказы


# --- Вспомогательные функции ---
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

    # Избранное
    user_favorites = favorites.get(email, [])
    favorite_items = [item for item in menu_items_list if item["id"] in user_favorites]

    # Корзина
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

    return render_template(
        "dashboard.html",
        name=user["name"],
        role=user["role"],
        menu_items=menu_items,
        favorite_items=favorite_items,
        cart_items=cart_items,
        total_price=total_price
    )


# --- АДМИН-ПАНЕЛЬ ---
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    user = users[session["user"]]
    if user["role"] != "Administrator":
        return redirect(url_for("dashboard"))

    return render_template(
        "admin_dashboard.html",
        name=user["name"],
        menu_items_list=menu_items_list,
        orders_list=orders_list,
        users=users
    )


# --- МЕНЮ БЛЮД ---
@app.route("/menu")
def menu():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    category = request.args.get('category', '')
    search = request.args.get('search', '')

    filtered_items = menu_items_list
    if category:
        filtered_items = [item for item in filtered_items if item['category'] == category]
    if search:
        search_lower = search.lower()
        filtered_items = [
            item for item in filtered_items
            if search_lower in item['name'].lower() or search_lower in item['description'].lower()
        ]

    user_favorites = favorites.get(session["user"], [])
    categories = get_categories()

    return render_template(
        "menu.html",
        menu_items=filtered_items,
        categories=categories,
        selected_category=category,
        search_query=search,
        user_favorites=user_favorites
    )


# --- ИЗБРАННОЕ ---
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

    return render_template("cart.html", cart_items=cart_items, total_price=total_price)


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


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: СОЗДАТЬ ЗАКАЗ ИЗ КОРЗИНЫ ---
def create_order_from_cart(user_email):
    user_cart = carts.get(user_email, {})
    if not user_cart:
        return None

    order = {
        "id": len(active_orders) + len(completed_orders) + 1,
        "user": user_email,
        "items": [],
        "total": 0,
        "status": "Активен"
    }

    total_price = 0
    for item_id, quantity in user_cart.items():
        menu_item = next((it for it in menu_items_list if it["id"] == item_id), None)
        if not menu_item:
            continue

        item_total = menu_item["price"] * quantity
        order["items"].append({
            "id": menu_item["id"],
            "name": menu_item["name"],
            "quantity": quantity,
            "price": menu_item["price"],
            "total": item_total
        })
        total_price += item_total

    order["total"] = total_price
    active_orders.append(order)
    carts[user_email] = {}  # очищаем корзину

    return order["id"]


# --- ОФОРМЛЕНИЕ ЗАКАЗА ---
@app.route('/checkout', methods=['POST'])
def checkout():
    user_email = session.get('user')
    if not user_email:
        flash('Сначала войдите в систему!', 'error')
        return redirect(url_for('index'))

    order_id = create_order_from_cart(user_email)
    if order_id is None:
        flash('Корзина пуста!', 'error')
        return redirect(url_for('cart'))

    flash(f'✅ Заказ #{order_id} успешно оформлен и отправлен в активные!', 'success')
    return redirect(url_for('orders_page'))


# --- ПОДТВЕРЖДЕНИЕ ЗАКАЗА ---
@app.route("/confirm_order", methods=["POST"])
def confirm_order():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    user_email = session["user"]
    user_cart = carts.get(user_email, {})
    if not user_cart:
        flash("Корзина пуста!", "error")
        return redirect(url_for("cart"))

    order = {
        "id": len(active_orders) + len(completed_orders) + 1,
        "user": user_email,
        "items": [],
        "total": 0,
        "status": "Активен"
    }

    total_price = 0
    for item_id, quantity in user_cart.items():
        for item in menu_items_list:
            if item["id"] == item_id:
                order["items"].append({
                    "name": item["name"],
                    "quantity": quantity,
                    "price": item["price"],
                    "total": item["price"] * quantity
                })
                total_price += item["price"] * quantity
                break

    order["total"] = total_price
    active_orders.append(order)
    carts[user_email] = {}
    flash("✅ Заказ подтверждён и отправлен в активные!", "success")
    return redirect(url_for("orders_page"))


# --- БЫСТРАЯ ПРОДАЖА ---
@app.route("/quick_sale", methods=["POST"])
def quick_sale():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    name = request.form.get("name")
    price = float(request.form.get("price", 0))

    if not name or price <= 0:
        flash("Некорректные данные для быстрой продажи!", "error")
        return redirect(url_for("menu"))

    order = {
        "id": len(active_orders) + len(completed_orders) + 1,
        "user": session["user"],
        "items": [{"name": name, "quantity": 1, "price": price, "total": price}],
        "total": price,
        "status": "Активен"
    }

    active_orders.append(order)
    flash(f"💸 Быстрая продажа: {name} ({price} сом) добавлена в активные заказы!", "success")
    return redirect(url_for("orders_page"))


# --- ВЫДАЧА ЗАКАЗА ---
@app.route("/complete/<int:order_id>")
def complete(order_id):
    for order in active_orders:
        if order["id"] == order_id:
            order["status"] = "Доставлен"
            completed_orders.append(order)
            active_orders.remove(order)
            flash(f"🚚 Заказ #{order_id} отмечен как доставленный!", "info")
            break

    return redirect(url_for("orders_page"))


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


# --- СТРАНИЦЫ ЗАКАЗОВ ---
@app.route("/orders")
def orders_page():
    if "user" not in session:
        return redirect(url_for("index"))

    user_email = session["user"]
    current_user_data = users[user_email]

    return render_template(
        "orders.html",
        active_orders=active_orders,
        completed_orders=completed_orders,
        current_user=current_user_data
    )


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


# --- ЗАПУСК ПРИЛОЖЕНИЯ ---
if __name__ == "__main__":
    print("🚀 ИС Столовая КГТУ запущена!")
    print("📍 Адрес: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
