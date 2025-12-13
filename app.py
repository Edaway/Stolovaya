from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(db_path)

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

# --- Категории меню ---
categories_list = ["Пицца", "Суши", "Бургеры", "Паста", "Салаты", "Напитки"]

# --- Пример заказов ---
orders_list = [
    {"id": 1, "dish": "Пицца Маргарита", "status": "Активен"},
    {"id": 2, "dish": "Суши сет Самурай", "status": "Активен"},
    {"id": 3, "dish": "Бургер Чеддер", "status": "Доставлен"},
]

# --- Меню блюд с категориями (в сомах) ---
menu_items_list = [
    {"id": 1, "name": "Пицца Маргарита", "price": 450, "category": "Пицца", "image": "🍕", "description": "Классическая пицца с томатным соусом и моцареллой", "hidden": False},
    {"id": 2, "name": "Суши сет Самурай", "price": 1200, "category": "Суши", "image": "🍣", "description": "Ассорти из свежих суши и роллов", "hidden": False},
    {"id": 3, "name": "Бургер Чеддер", "price": 350, "category": "Бургеры", "image": "🍔", "description": "Сочный бургер с сыром чеддер и овощами", "hidden": False},
    {"id": 4, "name": "Паста Карбонара", "price": 420, "category": "Паста", "image": "🍝", "description": "Итальянская паста с беконом и соусом", "hidden": False},
    {"id": 5, "name": "Салат Цезарь", "price": 280, "category": "Салаты", "image": "🥗", "description": "Классический салат с курицей и соусом цезарь", "hidden": False},
    {"id": 6, "name": "Кола", "price": 120, "category": "Напитки", "image": "🥤", "description": "Освежающий газированный напиток", "hidden": False},
]

# --- Хранилища данных ---
favorites = {}      # Избранное пользователей
carts = {}          # Корзины пользователей
active_orders = []  # Активные заказы
completed_orders = []  # Завершённые заказы
pre_orders = []     # Предзаказы

# --- Вспомогательные функции ---
def get_next_id():
    return max([item['id'] for item in menu_items_list], default=0) + 1

def get_categories():
    return categories_list

def get_user_orders(user_email):
    """Получить все заказы пользователя"""
    user_orders = []
    
    # Активные заказы
    for order in active_orders:
        if order["user"] == user_email:
            user_orders.append({**order, "type": "active"})
    
    # Предзаказы
    for order in pre_orders:
        if order["user"] == user_email:
            user_orders.append({**order, "type": "preorder"})
    
    # Завершенные заказы
    for order in completed_orders:
        if order["user"] == user_email:
            user_orders.append({**order, "type": "completed"})
    
    # Сортируем по ID в обратном порядке (новые сверху)
    return sorted(user_orders, key=lambda x: x["id"], reverse=True)

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

    filtered_items = [item for item in menu_items_list if not item.get("hidden", False)]
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
        "status": "Активен",
        "created_at": datetime.now().isoformat()  # Добавляем время создания
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

    # --- СПИСАНИЕ ПРОДУКТОВ ---
    #order = next((o for o in active_orders if o["id"] == order_id), None)
    #if order:
    #    for item in order["items"]:
    #        deduct_ingredients(item["id"], item["quantity"])
    # --------------------------

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
        "status": "Активен",
        "created_at": datetime.now().isoformat()  # Добавляем время создания
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

def save_order_to_analytics(order):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for item in order["items"]:
        cursor.execute("""
            INSERT INTO dish_stats (dish_name, quantity, total_price, sold_at)
            VALUES (?, ?, ?, ?)
        """, (
            item["name"],
            item["quantity"],
            item["total"],
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

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
        "status": "Активен",
        "created_at": datetime.now().isoformat()  # Добавляем время создания
    }

    active_orders.append(order)
    flash(f"💸 Быстрая продажа: {name} ({price} сом) добавлена в активные заказы!", "success")
    return redirect(url_for("orders_page"))

@app.route("/complete/<int:order_id>")
def complete(order_id):
    # ищем заказ
    for order in active_orders:
        if order["id"] == order_id:
            active_orders.remove(order)
            order["status"] = "Завершён"

            # 👉 сохраняем блюда в аналитику
            save_order_to_analytics(order)

            completed_orders.append(order)
            flash("Заказ выдан!", "success")
            return redirect(url_for("orders_page"))

    flash("Заказ не найден!", "error")
    return redirect(url_for("orders_page"))



def deduct_ingredients(dish_id, count):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Загружаем рецепт блюда
    cur.execute("SELECT product_id, amount FROM recipes WHERE dish_id = ?", (dish_id,))
    recipe = cur.fetchall()

    # Списываем
    for pid, amount in recipe:
        cur.execute("""
            UPDATE products 
            SET quantity = quantity - ?
            WHERE id = ?
        """, (amount * count, pid))

    conn.commit()
    conn.close()

# --- УПРАВЛЕНИЕ МЕНЮ ---
@app.route("/manage_menu", methods=["GET", "POST"])
def manage_menu():
    # Проверка прав
    if "user" not in session or users[session["user"]]["role"] != "Administrator":
        flash("⛔ Доступ запрещён!", "error")
        return redirect(url_for("dashboard"))

    # Если только зашли на страницу (GET), сразу отображаем HTML
    if request.method == "GET":
        categories = get_categories()
        return render_template("manage_menu.html", menu_items=menu_items_list, categories=categories)

    # Если POST — начинаем разбирать форму
    action = request.form.get("action")
    item_id = request.form.get("id")
    name = (request.form.get("name") or "").strip()
    price = request.form.get("price")
    category = request.form.get("category")
    new_category = (request.form.get("new_category") or "").strip()
    description = (request.form.get("description") or "").strip()

    # --- 1. Обработка новой категории ---
    if category == "new":
        if not new_category:
            flash("Введите название новой категории!", "error")
            return redirect(url_for("manage_menu"))
        elif new_category in categories_list:
            flash(f"Категория '{new_category}' уже существует!", "error")
            return redirect(url_for("manage_menu"))
        else:
            categories_list.append(new_category)
            category = new_category
            flash(f"Категория '{new_category}' успешно добавлена!", "success")

    # --- 2. Добавление блюда ---
    if action == "add":
        # Проверка на дубликаты по названию блюда
        for item in menu_items_list:
            if item["name"].strip().lower() == name.lower():
                flash(f"Блюдо '{name}' уже существует!", "error")
                return redirect(url_for("manage_menu"))

        try:
            price_val = float(price)
        except (ValueError, TypeError):
            flash("Неверное значение цены!", "error")
            return redirect(url_for("manage_menu"))

        new_item = {
            "id": get_next_id(),
            "name": name,
            "price": price_val,
            "category": category,
            "description": description,
            "hidden": False
        }
        menu_items_list.append(new_item)
        flash(f"✅ Блюдо '{name}' добавлено!", "success")

    # --- 3. Редактирование блюда ---
    elif action == "edit":
        for item in menu_items_list:
            if str(item["id"]) == item_id:
                # Проверка: изменяем имя → не должно совпадать с другим блюдом
                for other in menu_items_list:
                    if other["id"] != item["id"] and other["name"].lower() == name.lower():
                        flash(f"Блюдо с названием '{name}' уже существует!", "error")
                        return redirect(url_for("manage_menu"))

                item["name"] = name
                item["category"] = category
                item["description"] = description
                try:
                    item["price"] = float(price)
                except:
                    pass
                flash(f"✏️ Блюдо '{item['name']}' обновлено!", "success")
                break

    elif action == "delete":
        menu_items_list[:] = [item for item in menu_items_list if str(item["id"]) != item_id]
        flash("Блюдо удалено!", "info")

    elif action == "hide":
        for item in menu_items_list:
            if str(item["id"]) == item_id:
                item["hidden"] = True
                flash(f"✅ Блюдо '{item['name']}' скрыто!", "info")
                break

    elif action == "show":
        for item in menu_items_list:
            if str(item["id"]) == item_id:
                item["hidden"] = False
                flash(f"✅ Блюдо '{item['name']}' снова отображается!", "success")
                break

    categories = get_categories()
    return redirect(url_for("manage_menu"))

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

# --- ИСТОРИЯ ЗАКАЗОВ ---
@app.route("/history")
def history():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    user_email = session["user"]
    user_orders = get_user_orders(user_email)
    
    return render_template("history.html", orders=user_orders)

# --- СТРАНИЦА ПРЕДЗАКАЗА ---
@app.route("/preorder")
def preorder_page():
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

    return render_template(
        "preorder.html",
        cart_items=cart_items,
        total_price=total_price
    )

# --- СОЗДАНИЕ ПРЕДЗАКАЗА ---
@app.route("/create_preorder", methods=["POST"])
def create_preorder():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    user_email = session["user"]
    user_cart = carts.get(user_email, {})
    
    if not user_cart:
        flash("Корзина пуста!", "error")
        return redirect(url_for("cart"))

    date = request.form.get("date")
    time = request.form.get("time")
    
    if not date or not time:
        flash("Укажите дату и время получения!", "error")
        return redirect(url_for("preorder_page"))

    # ПРОВЕРКА ДАТЫ - ДОБАВЛЕНО!
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        today = datetime.now().date()
        if selected_date < today:
            flash("Нельзя выбрать прошедшую дату!", "error")
            return redirect(url_for('preorder_page'))
    except ValueError:
        flash("Неверный формат даты!", "error")
        return redirect(url_for('preorder_page'))

    # Создаем предзаказ
    order = {
        "id": len(active_orders) + len(completed_orders) + len(pre_orders) + 1,
        "user": user_email,
        "items": [],
        "total": 0,
        "status": "Предзаказ",
        "date": date,
        "time": time,
        "created_at": datetime.now().isoformat()
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
    pre_orders.append(order)
    carts[user_email] = {}  # очищаем корзину
    
    flash(f"✅ Предзаказ #{order['id']} создан на {date} в {time}!", "success")
    return redirect(url_for("history"))

# --- ОТМЕНА ЗАКАЗА ---
@app.route("/cancel_order/<int:order_id>")
def cancel_order(order_id):
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    user_email = session["user"]
    
    # Ищем в активных заказах
    for order in active_orders:
        if order["id"] == order_id and order["user"] == user_email:
            order["status"] = "Отменен"
            completed_orders.append(order)
            active_orders.remove(order)
            flash(f"❌ Заказ #{order_id} отменен!", "info")
            return redirect(url_for("history"))
    
    # Ищем в предзаказах
    for order in pre_orders:
        if order["id"] == order_id and order["user"] == user_email:
            order["status"] = "Отменен"
            completed_orders.append(order)
            pre_orders.remove(order)
            flash(f"❌ Предзаказ #{order_id} отменен!", "info")
            return redirect(url_for("history"))
    
    flash("Заказ не найден или у вас нет прав для его отмены!", "error")
    return redirect(url_for("history"))

@app.route("/warehouse", methods=["GET", "POST"])
def warehouse():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")

        # Добавление нового продукта
        if action == "add_product":
            name = request.form["name"]
            qty = float(request.form["quantity"])
            unit = request.form["unit"]
            cur.execute("INSERT INTO products (name, quantity, unit) VALUES (?, ?, ?)",
                        (name, qty, unit))

        # Приход товара
        elif action == "add_stock":
            pid = request.form["product_id"]
            qty = float(request.form["quantity"])
            cur.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (qty, pid))

        # Ручное списание
        elif action == "remove_stock":
            pid = request.form["product_id"]
            qty = float(request.form["quantity"])
            cur.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (qty, pid))

        elif action == "delete_product":
            pid = request.form["product_id"]
            cur.execute("DELETE FROM products WHERE id = ?", (pid,))
            flash("Продукт удалён!", "info")

        conn.commit()

    cur.execute("SELECT id, name, quantity, unit FROM products")
    products = cur.fetchall()

    conn.close()
    return render_template("warehouse.html", products=products)

@app.route("/recipe_editor/<int:dish_id>", methods=["GET", "POST"])
def recipe_editor(dish_id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Получаем блюдо из menu_items_list
    dish = next((item for item in menu_items_list if item["id"] == dish_id), None)
    if dish is None:
        flash("Блюдо не найдено!", "error")
        return redirect(url_for("manage_menu"))
    dish_name = dish["name"]

    if request.method == "POST":
        # Удаляем старый рецепт
        cur.execute("DELETE FROM recipes WHERE dish_id = ?", (dish_id,))

        # Добавляем новый рецепт
        for pid, amount in request.form.items():
            if not amount or float(amount) <= 0:
                continue
            cur.execute(
                "INSERT INTO recipes (dish_id, product_id, amount) VALUES (?, ?, ?)",
                (dish_id, pid, float(amount))
            )

        conn.commit()
        flash("Рецепт обновлён", "success")
        return redirect(url_for("recipe_editor", dish_id=dish_id))

    # Загружаем продукты
    cur.execute("SELECT id, name, unit FROM products")
    products = cur.fetchall()

    # Загружаем текущий рецепт
    cur.execute("SELECT product_id, amount FROM recipes WHERE dish_id = ?", (dish_id,))
    recipe = dict(cur.fetchall())  # {product_id: amount}

    conn.close()

    return render_template("recipe_editor.html", products=products, recipe=recipe, dish_name=dish_name)

@app.route("/products")
def show_products():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    conn.close()
    return render_template("products.html", products=products)

@app.route("/analytics")
def analytics():
    if "user" not in session or users[session["user"]]["role"] != "Administrator":
        flash("⛔ Доступ запрещён!", "error")
        return redirect(url_for("dashboard"))

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    query = "SELECT dish_name, quantity, total_price, sold_at FROM dish_stats WHERE 1=1"
    params = []

    if date_from:
        query += " AND date(sold_at) >= date(?)"
        params.append(date_from)

    if date_to:
        query += " AND date(sold_at) <= date(?)"
        params.append(date_to)

    query += " ORDER BY sold_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()

    stats = [{
        "dish_name": r[0],
        "quantity": r[1],
        "total_price": r[2],
        "sold_at": r[3][:10]
    } for r in rows]

    # Общая выручка и количество
    total_income = sum(r["total_price"] for r in stats)
    total_qty = sum(r["quantity"] for r in stats)

    # ТОП-5 блюд
    cur.execute("""
        SELECT dish_name, SUM(quantity) as qty
        FROM dish_stats
        GROUP BY dish_name
        ORDER BY qty DESC
        LIMIT 5
    """)
    top_dishes = cur.fetchall()

    # График продаж по дням
    cur.execute("""
        SELECT date(sold_at), SUM(total_price)
        FROM dish_stats
        GROUP BY date(sold_at)
        ORDER BY date(sold_at)
    """)
    sales_by_day = cur.fetchall()

    conn.close()

    return render_template(
        "analytics.html",
        stats=stats,
        total_income=total_income,
        total_qty=total_qty,
        top_dishes=top_dishes,
        sales_by_day=sales_by_day,
        date_from=date_from,
        date_to=date_to
    )


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