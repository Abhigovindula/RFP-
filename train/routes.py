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
        # Get payment details
        name = request.form.get('name')
        cvv = request.form.get('cvv')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        
        # Get passenger and journey details from session
        passengers = session.get('passengers', [])
        train_no = session.get('train_no')
        train_name = session.get('train_name')
        from_station = session.get('from_station')
        to_station = session.get('to_station')
        date = session.get('date')
        
        # Get fare information from the database
        conn = sqlite3.connect("trains.db")
        cursor = conn.cursor()
        query = """
            SELECT General_Fare, Sleeper_Fare, AC_Fare
            FROM train_schedule
            WHERE Train_No = ? AND Station_Name = ? AND Destination_Station_Name = ?
        """
        cursor.execute(query, (train_no, from_station, to_station))
        fares = cursor.fetchone()
        conn.close()
        
        if fares:
            general_fare, sleeper_fare, ac_fare = fares
            
            # Calculate fare for each passenger and update the passenger data
            for passenger in passengers:
                if passenger['class'] == 'general':
                    passenger['fare'] = general_fare
                elif passenger['class'] == 'sleeper':
                    passenger['fare'] = sleeper_fare
                else:  # AC class
                    passenger['fare'] = ac_fare
            
            # Update the passengers in session with fare information
            session['passengers'] = passengers
        
        # Store payment details in session
        session['payment_details'] = {
            'name': name,
            'card_number': card_number[-4:],  # Store only last 4 digits
            'expiry_date': expiry_date
        }
        
        # Redirect to ticket details page
        return redirect(url_for('ticket_details'))
    
    return render_template('payment.html')

@app.route('/ticket_details')
def ticket_details():
    # Get all details from session
    passengers = session.get('passengers', [])
    train_no = session.get('train_no')
    train_name = session.get('train_name')
    from_station = session.get('from_station')
    to_station = session.get('to_station')
    date = session.get('date')
    payment_details = session.get('payment_details', {})
    
    # Calculate total fare
    total_fare = sum(passenger.get('fare', 0) for passenger in passengers)
    
    # Check if all required data is present
    if not all([passengers, train_no, train_name, from_station, to_station, date]):
        flash("Error: Missing booking information. Please try again.", "danger")
        return redirect(url_for('home'))
    
    return render_template('ticket_details.html',
                         passengers=passengers,
                         train_no=train_no,
                         train_name=train_name,
                         from_station=from_station,
                         to_station=to_station,
                         date=date,
                         payment_details=payment_details,
                         total_fare=total_fare)

@app.route("/add_passengers", methods=["GET", "POST"])
def add_passengers():
    if request.method == "GET":
        train_no = request.args.get("train_no")
        train_name = request.args.get("train_name")
        from_station = request.args.get("from_station")
        to_station = request.args.get("to_station")
        date = request.args.get("date")

        # Get fare information from the database
        conn = sqlite3.connect("trains.db")
        cursor = conn.cursor()
        query = """
            SELECT General_Fare, Sleeper_Fare, AC_Fare
            FROM train_schedule
            WHERE Train_No = ? AND Station_Name = ? AND Destination_Station_Name = ?
        """
        cursor.execute(query, (train_no, from_station, to_station))
        fares = cursor.fetchone()
        conn.close()

        if fares:
            general_fare, sleeper_fare, ac_fare = fares
        else:
            flash("Train information not found.", "danger")
            return redirect(url_for("dashboard"))

        return render_template("add_passengers.html",
                             train_no=train_no,
                             train_name=train_name,
                             from_station=from_station,
                             to_station=to_station,
                             date=date,
                             general_fare=general_fare,
                             sleeper_fare=sleeper_fare,
                             ac_fare=ac_fare,
                             total_fare=0)

    elif request.method == "POST":
        # Get the number of passengers
        num_passengers = int(request.form.get("num_passengers"))
        passengers = []

        # Get fare information from the database
        train_no = request.form.get("train_no")
        from_station = request.form.get("from_station")
        to_station = request.form.get("to_station")
        
        conn = sqlite3.connect("trains.db")
        cursor = conn.cursor()
        query = """
            SELECT General_Fare, Sleeper_Fare, AC_Fare
            FROM train_schedule
            WHERE Train_No = ? AND Station_Name = ? AND Destination_Station_Name = ?
        """
        cursor.execute(query, (train_no, from_station, to_station))
        fares = cursor.fetchone()
        conn.close()

        if fares:
            general_fare, sleeper_fare, ac_fare = fares
        else:
            flash("Train information not found.", "danger")
            return redirect(url_for("dashboard"))

        # Collect passenger details and calculate fare
        for i in range(1, num_passengers + 1):
            passenger_class = request.form.get(f"passenger_{i}_class")
            fare = 0
            if passenger_class == 'general':
                fare = general_fare
            elif passenger_class == 'sleeper':
                fare = sleeper_fare
            else:  # AC class
                fare = ac_fare

            passenger = {
                "name": request.form.get(f"passenger_{i}_name"),
                "age": request.form.get(f"passenger_{i}_age"),
                "gender": request.form.get(f"passenger_{i}_gender"),
                "phone": request.form.get(f"passenger_{i}_phone"),
                "class": passenger_class,
                "fare": fare
            }
            passengers.append(passenger)

        # Store passenger details in session for payment page
        session["passengers"] = passengers
        session["train_no"] = train_no
        session["train_name"] = request.form.get("train_name")
        session["from_station"] = from_station
        session["to_station"] = to_station
        session["date"] = request.form.get("date")

        return redirect(url_for("payment"))
