from flask import redirect,render_template,url_for,flash,request,session
from train import db,app,bcrypt
from train.models import User
import sqlite3

# Routes
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
        else:
            new_user = User(name=name, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("trains.db")
    cursor = conn.cursor()

    # Get unique station names from the database
    cursor.execute("SELECT DISTINCT Station_Name FROM train_schedule")
    stations = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template("dashboard.html", name=session["user_name"], stations=stations)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/about")
def about():
    return render_template("about.html")



@app.route('/carousel')
def carousel_page():
    return render_template('carousel.html')

@app.route("/results", methods=["GET"])
def results():
    from_station = request.args.get("from")
    to_station = request.args.get("to")
    date = request.args.get("date")

    conn = sqlite3.connect("trains.db")
    cursor = conn.cursor()

    # Query trains between selected stations
    query = """
        SELECT Train_No, Train_Name, Arrival_Time, Departure_Time, Distance, General_Fare, Sleeper_Fare, AC_Fare
        FROM train_schedule
        WHERE Station_Name = ? AND Destination_Station_Name = ?
    """
    cursor.execute(query, (from_station, to_station))
    trains = cursor.fetchall()
    
    conn.close()

    return render_template("results.html", trains=trains, from_station=from_station, to_station=to_station, date=date)



@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        name = request.form.get('name')
        cvv = request.form.get('cvv')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        return "Payment Successful!"
    
    return render_template('payment.html')
