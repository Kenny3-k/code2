from flask import Flask, url_for,redirect,request,render_template, flash, jsonify

from flask_login import LoginManager, login_user,logout_user, login_required, UserMixin, current_user
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests

app=Flask(__name__)

app.secret_key = 'bQ8v!fT@G$k9xLz#1uM4vC7wP2sJhXoE'
API_BASE = "https://api.carbonintensity.org.uk"

#configure sqlite database
basedir= os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{os.path.join(basedir,'rolsa3.db' )}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db=SQLAlchemy(app)

#set up flask login
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#creating user
class User1(UserMixin, db.Model):
    id= db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash=db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        """Hash and store the password"""
        self.password_hash =  generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify the given password against the hash"""
        return check_password_hash(self.password_hash, password)
    
class EnergyUsuage(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user1.id'), nullable=False)
    electricity_kwh=db.Column(db.Float, nullable=False, default=0)
    transport_km=db.Column(db.Float, nullable=False, default=0)
    gas_kg=db.Column(db.Float, nullable=False, default=0)
    timestamp= db.Column(db.DateTime, server_default=db.func.now())
    #This serialize method is used to convert an object's attribute into a JSON friendly dictionary,
    #formatting the date and keeping only simple data types

    def serialize(self):
        return {
            'date':self.timestamp.strftime('%d/%m/%Y') if self.timestamp else None,
            'electricity_kwh': self.electricity_kwh,
            'transport_km': self.transport_km,
            'gas_kg': self.gas_kg
        }
    
class CarbonRecord(db.Model):
    __tablename__='carbon_record'
    id= db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user1.id'))
    electricity=db.Column(db.Float)
    fuel=db.Column(db.Float)
    distance=db.Column(db.Float)
    has_solar=db.Column(db.Boolean)
    total_emissions=db.Column(db.Float)

class Schedule(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('user1.id'), nullable=False)
    title=db.Column(db.String(200), nullable=False)
    start_time=db.Column(db.String(50), nullable=False)
    end_time=db.Column(db.String(50), nullable=False)
    description=db.Column(db.Text)
    date=db.Column(db.Date)

    def serialize(self):
        return {
            'id':self.id,
            'title':self.title,
            'date':self.date.strftime('%d/%m/%Y') if self.date else None,
            'start_time':self.time.strftime,
            'end_time':self.time.strftime,
            'description':self.description
        }
    
@login_manager.user_loader
def load_user(user_id):
    user=User1.query.all()
    return User1.query.get(int(user_id))

@app.route('/')
def index():
    users=User1.query.all()
    return render_template('index.html', users=users, user=current_user)

@app.route('/add_user', methods=['POST'])
def add_user():
    email=request.form.get('email')
    name=request.form.get('name')
    password=request.form.get('password')

    if email and password:
        existing_user=User1.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exist")
            return redirect(url_for('registration'))

        new_user=User1(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("User registered successfully, Please log in")
        return redirect(url_for('login'))
    
    flash("Email and password required")
    return redirect (url_for('registration'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email')
        password= request.form.get('password')
        user= User1.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome,{user.name or user.email}!", "success")
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/success/<email>')
def success(email):
    return render_template('index.html')

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/schedule')
def schedule_page():
    schedules=Schedule.query.filter_by(user_id=current_user.id).order_by(Schedule.start_time).all()
    return render_template('schedule.html',schedules=schedules, user1=current_user)

@app.route('/appointment')
@login_required
def appointment():
    appointments = Schedule.query.filter_by(user_id=current_user.id).all()
    return render_template('appointment.html', appointments=appointments, user=current_user)

@app.route('/submit_energy', methods=['POST'])
@login_required
def submit_energy():
    try:
        data= request.get_json(silent=True) or request.form

        #validating and converting input values safely
        electricity_kwh= float(data.get('electricity_kwh', 0)or 0)
        transport_km= float(data.get('transport_km', 0)or 0)
        gas_kg= float(data.get('gas_kg', 0)or 0)

        #creating a new energy record
        usuage= EnergyUsuage(
            user_id= current_user.id,
            electricity_kwh= electricity_kwh,
            transport_km= transport_km,
            gas_kg= gas_kg
        )
        #save to database
        db.session.add(usuage)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Energy data saved successfully'}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400
    
#Carbon Calcualtor
@app.route('/calculate', methods=['POST'])
@login_required
def calculate():
    electricity= float(request.form['electricity'])
    fuel= float(request.form['fuel'])
    distance= float(request.form['distance'])
    has_solar= request.form.get('solar') == 'yes'

    electricity_factor= 0.92
    fuel_factor= 2.31
    driving_factor= 0.12

    electricity_emissions= electricity*electricity_factor
    fuel_emissions=fuel*fuel_factor
    driving_emissions=distance*driving_factor

    total_emissions= electricity_emissions + fuel_emissions + driving_emissions

    if has_solar:
        total_emissions*=0.08

    try:
        usuage=EnergyUsuage(
            user_id=current_user.id,
            electricity_kwh=electricity,
            transport_km=distance,
            gas_kg=fuel
        )

        record= CarbonRecord(
        user_id= current_user.id,
        electricity=electricity,
        fuel=fuel,
        distance=distance,
        has_solar=has_solar,
        total_emissions=total_emissions
        )
        db.session.add(record)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f"Error saving data:{str(e)}", "danger")
        return redirect(url_for('calculator'))

    suggestion=[]
    if not has_solar:
        suggestion.append('Install solar panels to reduce emissions.')
    if fuel > 0:
        suggestion.append('Switch to an electric vehicle.')
    suggestion.append('Use smart home systems to optimize energy usuage.')

    return render_template(
        'results.html',
        total= round(total_emissions, 2),
        electricity_emissions=round(electricity_emissions, 2),
        fuel_emissions=round(fuel_emissions, 2),
        driving_emissions= round(driving_emissions, 2),
        suggestion=suggestion
    )

#dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    records=CarbonRecord.query.filter_by(user_id=current_user.id).all()
    labels= [f"Record {r.id}" for r in records]
    values= [r.total_emissions for r in records]
    return render_template(
        'dashboard.html',
        labels=labels,
        values=values,
        user=current_user
    )

@app.route("/api/v1/live-carbon-chart", methods=["GET"])
def live_carbon_chart():
    date= request.args.get("date")
    endpoint= f"/intensity/date/{date}" if date else"/intensity"

    resp= requests.get(f"{API_BASE}{endpoint}")
    if resp.status_code!= 200:
        return jsonify({"error": "Failed to fetch data"}), 500
    
    raw= resp.json()["data"]

    labels= []
    values= []

    for item in raw:
        labels.append(item["from"][11:16])
        values.append(item["intensity"]["actual"] or item["intensity"]["forecast"])

    return jsonify({
        "unit": "gCO2e/kWh",
        "labels": labels,
        "values": values,
        "source": "UK National Grid Carbon Instensity API"
    })


@app.route('/charts')
def charts():
    records=CarbonRecord.query.all()
    labels= [f"Record {r.id}" for r in records]
    values= [r.total_emissions for r in records]
    return render_template('charts.html', labels=labels, values=values, user=current_user)

@app.route('/calculator')
def calculator():
    return render_template('calculate.html')

@app.route('/privacy')
def privacy():
    return render_template('privacypolicy.html')

@app.route('/schedule', methods=['POST'])
@login_required
def schedule():
    title=request.form.get('title')
    start_time=request.form.get('start_time')
    end_time=request.form.get('end_time')
    date=datetime.strptime(request.form.get('date'), '%d/%m/%Y').date()
    description=request.form.get('description')

    if not title or not start_time or not end_time:
        flash("Title and Time are required")
        return redirect(url_for('schedule'))
    
    try:
        new_schedule= Schedule(
            user_id=current_user.id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            date=date
        )
        db.session.add(new_schedule)
        db.session.commit()
        flash("Schedule has been added succesfully!!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving schedule: {str(e)}")
    return redirect(url_for('schedule_page'))

if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.debug=True
    app.run()

