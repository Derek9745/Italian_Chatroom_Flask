from flask_login import LoginManager, UserMixin, login_required, logout_user, login_user, current_user
from flask import Flask, render_template, session, url_for, redirect, request,flash
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = "home"  # Redirect here if not logged in
login_manager.init_app(app)

socketio = SocketIO(app)

# SQLAlchemy configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Database model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Flask-Login user loader function
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Routes
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('lobby'))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    user = Users.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for("lobby"))
    else:
        return render_template("index.html", error="Invalid username or password")


# Register new user
@app.route('/register', methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    user = Users.query.filter_by(username=username).first()
    if user:
        return render_template("index.html", error="User already exists!")
    else:
        new_user = Users(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)  # Log the user in after successful registration
        return redirect(url_for('lobby'))


# Lobby - protected route
@app.route('/lobby')
@login_required
def lobby():
    return render_template("lobby.html", username=current_user.username)


# Logout route
@app.route("/logout",methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Make sure the database tables are created
    socketio.run(app, debug=True)
