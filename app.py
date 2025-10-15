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

# Меню блюд
menu_items_list = [
    {"id": 1, "name": "Пицца Маргарита", "price": 450},
    {"id": 2, "name": "Суши сет Самурай", "price": 1200},
    {"id": 3, "name": "Бургер Чеддер", "price": 350},
]

def get_next_id():
    return max([item['id'] for item in menu_items_list], default=0) + 1

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

# --- ПАНЕЛЬ ПОЛЬЗОВАТЕЛЯ ---
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Сначала войдите в систему!", "error")
        return redirect(url_for("index"))

    email = session["user"]
    user = users[email]
    
    menu_items = [
        ("Меню блюд", "menu"),
        ("Корзина", "cart"),
        ("Мои заказы", "orders_page"),
        ("История заказов", "history"),
        ("Выход", "logout")
    ]

    return render_template("dashboard.html", name=user["name"], role=user["role"], menu_items=menu_items)

# --- АДМИН-ПАНЕЛЬ ---
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    user = users[session["user"]]
    if user["role"] != "Administrator":
        return redirect(url_for("dashboard"))

    return render_template("admin_dashboard.html", name=user["name"])

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

        if action == "add":
            menu_items_list.append({"id": get_next_id(), "name": name, "price": float(price)})
            flash(f"Блюдо '{name}' добавлено!", "success")
        elif action == "edit":
            for item in menu_items_list:
                if str(item["id"]) == item_id:
                    item["name"] = name
                    item["price"] = float(price)
                    flash(f"Блюдо '{name}' обновлено!", "success")
        elif action == "delete":
            menu_items_list[:] = [item for item in menu_items_list if str(item["id"]) != item_id]
            flash("Блюдо удалено!", "info")

    return render_template("manage_menu.html", menu_items=menu_items_list)

# --- ОСТАЛЬНЫЕ СТРАНИЦЫ ---
@app.route("/menu")
def menu():
    return "<h2>🍽️ Меню блюд</h2><a href='/dashboard'>Назад</a>"

@app.route("/cart")
def cart():
    return "<h2>🛒 Корзина</h2><a href='/dashboard'>Назад</a>"

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