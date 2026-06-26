from flask import Flask, render_template, request, redirect, session
from db_config import db
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "carbon_secret"


# ================= HOME =================
@app.route('/')
def home():
    return render_template("index.html")


# ================= LOGIN =================
@app.route('/login', methods=['GET','POST'])
def login():

    cursor = db.cursor(dictionary=True, buffered=True)

    error = None

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email,password)
        )

        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            return redirect('/dashboard')
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)


# ================= REGISTER =================
@app.route('/register', methods=['GET','POST'])
def register():

    cursor = db.cursor(dictionary=True, buffered=True)

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor.execute(
            "INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
            (username,email,password)
        )

        db.commit()

        return redirect('/login')

    return render_template("register.html")


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor(dictionary=True, buffered=True)

    user_id = session['user_id']

    cursor.execute(
        "SELECT * FROM actions WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )

    actions = cursor.fetchall()

    return render_template("dashboard.html", actions=actions)


# ================= ADD ACTION =================
@app.route('/add_action', methods=['POST'])
def add_action():

    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor(dictionary=True, buffered=True)

    user_id = session['user_id']

    category = request.form['category']
    action_type = request.form['action_type']
    value = float(request.form['value'])

    carbon_saved = value * 0.21

    cursor.execute(
        "INSERT INTO actions (user_id,category,action_type,value,carbon_saved) VALUES (%s,%s,%s,%s,%s)",
        (user_id,category,action_type,value,carbon_saved)
    )

    db.commit()

    return redirect('/dashboard')


# ================= PROFILE =================
@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor(dictionary=True, buffered=True)

    user_id = session['user_id']

    cursor.execute("""
        SELECT category, SUM(carbon_saved) AS total
        FROM actions
        WHERE user_id=%s
        GROUP BY category
    """, (user_id,))
    data = cursor.fetchall()

    cursor.execute(
        "SELECT SUM(carbon_saved) AS total FROM actions WHERE user_id=%s",
        (user_id,)
    )
    total = cursor.fetchone()['total'] or 0

    cursor.execute(
        "SELECT COUNT(*) AS count FROM actions WHERE user_id=%s",
        (user_id,)
    )
    count = cursor.fetchone()['count']

    badges = []

    if total >= 10:
        badges.append("🌱 Beginner Eco Saver")
    if total >= 50:
        badges.append("🌿 Green Warrior")
    if total >= 100:
        badges.append("🌍 Climate Champion")

    if not badges:
        badges.append("Start your journey 🌱")

    # STREAK
    cursor.execute("""
        SELECT DATE(created_at) as action_date
        FROM actions
        WHERE user_id=%s
        ORDER BY action_date DESC
    """, (user_id,))
    dates = [row['action_date'] for row in cursor.fetchall()]

    streak = 0
    if dates:
        unique_dates = list(dict.fromkeys(dates))
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        for i, date_str in enumerate(unique_dates):
            action_date = datetime.strptime(str(date_str), "%Y-%m-%d").date()

            if i == 0:
                if action_date == today or action_date == yesterday:
                    streak += 1
                else:
                    break
            else:
                prev_date = datetime.strptime(str(unique_dates[i-1]), "%Y-%m-%d").date()
                if (prev_date - action_date).days == 1:
                    streak += 1
                else:
                    break

    # 🔥 FIX ADDED (IMPORTANT)
    cursor.execute("""
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
               SUM(carbon_saved) as total
        FROM actions
        WHERE user_id=%s
        GROUP BY month
        ORDER BY month
    """, (user_id,))
    monthly_data = cursor.fetchall()

    cursor.execute("""
        SELECT WEEK(created_at) as week,
               SUM(carbon_saved) as total
        FROM actions
        WHERE user_id=%s
        GROUP BY week
    """, (user_id,))
    weekly_data = cursor.fetchall()

    cursor.execute("""
        SELECT YEAR(created_at) as year,
               SUM(carbon_saved) as total
        FROM actions
        WHERE user_id=%s
        GROUP BY year
    """, (user_id,))
    yearly_data = cursor.fetchall()

    # 🔥 ALREADY ADDED
    current_hour = datetime.now().hour

    return render_template(
        "profile.html",
        data=data or [],
        count=count,
        total=total,
        streak=streak,
        badges=badges,
        username=session.get('username'),
        current_hour=current_hour,
        monthly_data=monthly_data or [],   # 🔥 FIX
        weekly_data=weekly_data or [],     # 🔥 FIX
        yearly_data=yearly_data or []      # 🔥 FIX
    )

# ================= STATIC =================
@app.route('/travel')
def travel():
    return render_template("travel.html")

@app.route('/energy')
def energy():
    return render_template("energy.html")

@app.route('/food')
def food():
    return render_template("food.html")

@app.route('/waste')
def waste():
    return render_template("waste.html")


# ================= OTHER =================
@app.route('/suggestion')
def suggestion():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("suggestion.html")

@app.route('/about')
def about():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("about.html")


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= ADMIN =================
@app.route('/admin')
def admin():

    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'admin':
        return redirect('/dashboard')

    cursor = db.cursor(dictionary=True, buffered=True)

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    cursor.execute("SELECT SUM(carbon_saved) AS total_co2 FROM actions")
    total_co2 = cursor.fetchone()['total_co2'] or 0

    cursor.execute("SELECT COUNT(*) AS total_actions FROM actions")
    total_actions = cursor.fetchone()['total_actions']

    cursor.execute("SELECT * FROM users")
    user_list = cursor.fetchall()

    cursor.execute("SELECT * FROM actions ORDER BY id DESC")
    actions_list = cursor.fetchall()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_co2=total_co2,
        total_actions=total_actions,
        user_list=user_list,
        actions_list=actions_list
    )


# ================= DELETE =================
@app.route('/delete_user/<int:id>')
def delete_user(id):

    if session.get('role') != 'admin':
        return redirect('/dashboard')

    cursor = db.cursor(dictionary=True, buffered=True)

    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    db.commit()

    return redirect('/admin')


@app.route('/delete_action/<int:id>')
def delete_action(id):

    if session.get('role') != 'admin':
        return redirect('/dashboard')

    cursor = db.cursor(dictionary=True, buffered=True)

    cursor.execute("DELETE FROM actions WHERE id=%s", (id,))
    db.commit()

    return redirect('/admin')


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)