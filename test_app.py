from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "testsecret"

# Простая база пользователей
users = {
    "admin@stolovaya.kg": {"name": "Админ", "password": "admin123", "role": "Administrator"},
    "user@test.com": {"name": "Тест", "password": "123", "role": "Customer"}
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        print(f"📧 Email: {email}, 🔑 Password: {password}")
        
        if email in users and users[email]["password"] == password:
            session["user"] = email
            print("✅ Успешный вход!")
            return redirect("/dashboard")
        else:
            print("❌ Ошибка входа")
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Тест</title></head>
    <body>
        <h1>Тестовая форма</h1>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" value="user@test.com" required>
            <input type="password" name="password" placeholder="Пароль" value="123" required>
            <button type="submit">Войти</button>
        </form>
        <p>Тестовые данные: user@test.com / 123</p>
    </body>
    </html>
    ''')

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    
    user = users[session["user"]]
    return f"<h1>Добро пожаловать, {user['name']}!</h1><a href='/logout'>Выйти</a>"

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=5001)