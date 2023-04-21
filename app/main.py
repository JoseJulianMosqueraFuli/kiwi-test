import unittest
import math
import firebase_admin
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    flash,
    make_response,
    jsonify,
)
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from firebase_admin import firestore, credentials, initialize_app, auth
from flask_cors import CORS

from werkzeug.security import generate_password_hash
from flask_login import UserMixin, login_user, LoginManager

app = Flask(__name__)
bootstrap = Bootstrap(app)
CORS(app)
login_manager = LoginManager(app)


app.config["SECRET_KEY"] = "secret_key_here"

cred = credentials.Certificate("./keys.json")
firebase_admin.initialize_app(
    cred, {"databaseURL": "https://kiwibot-firebase-default-rtdb.firebaseio.com/"}
)


class LoginForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Enviar")


db = firestore.client()


def get_users():
    return db.collection("users").get()


def get_user(user_id):
    return db.collection("users").document(user_id).get()


def user_put(user_data):
    user_ref = db.collection("users").document(user_data.username)
    user_ref.set({"password": user_data.password})


class UserData:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class UserModel(UserMixin):
    def __init__(self, user_data):
        """
        :param user_data: UserData
        """
        self.id = user_data.username
        self.password = user_data.password

    @staticmethod
    def query(user_id):
        user_doc = get_user(user_id)
        user_data = UserData(
            username=user_doc.id, password=user_doc.to_dict()["password"]
        )

        return UserModel(user_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    context = {"login_form": login_form}

    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data

        user_doc = get_user(username)

        if user_doc.to_dict() is not None:
            password_from_db = user_doc.to_dict()["password"]

            if password == password_from_db:
                user_data = UserData(username, password)
                user = UserModel(user_data)

                login_user(user)

                flash("Bienvenido de nuevo")

                redirect(url_for("dashboard"))
            else:
                flash("La informaición no coincide")
        else:
            flash("El usario no existe")

        return redirect(url_for("index"))

    return render_template("login.html", **context)


@app.route("/signup", methods=["GET", "POST"])
def singup():
    signup_form = LoginForm()
    context = {"signup_form": signup_form}

    if signup_form.validate_on_submit():
        username = signup_form.username.data
        password = signup_form.password.data

        user_doc = get_user(username)

        if user_doc.to_dict() is None:
            password_hash = generate_password_hash(password)
            user_data = UserData(username, password_hash)
            user_put(user_data)

            user_model = UserModel(user_data)

            user = auth.create_user(
                email=username,
                email_verified=False,
                password=password_hash,
                display_name=username,
            )
            print("Sucessfully created new user: {0}".format(user.uid))

            login_user(user_model)

            flash("Bienvenido!")

            return redirect(url_for("dashboard"))

        else:
            flash("El usario existe!")

    return render_template("signup.html", **context)


@app.cli.command()
def test():
    tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner().run(tests)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html", error=error)


@app.errorhandler(500)
def no_server(error):
    return render_template("500.html", error=error)


@app.route("/")
def index():
    response = make_response(redirect("/dashboard"))
    return response


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    # return 'Welcome tu login bots'
    login_form = LoginForm()

    context = {"login_form": login_form}
    if login_form.validate_on_submit():
        username = login_form.username.data
        session["username"] = username

        flash("Nombre de usario registrado con éxito!")

        return redirect(url_for("index"))

    return render_template("dashboard.html", **context)


delivery_ref = db.collection("deliveries")
bots_ref = db.collection("bots")


@app.route("/deliveries", methods=["POST"])
def create_delivery():
    data = request.json
    delivery = {
        "id": data["id"],
        "creation_date": data["creation_date"],
        "state": data["state"],
        "pickup": {
            "pickup_lat": data["pickup"]["pickup_lat"],
            "pickup_lon": data["pickup"]["pickup_lon"],
        },
        "dropoff": {
            "dropoff_lat": data["dropoff"]["dropoff_lat"],
            "dropoff_lon": data["dropoff"]["dropoff_lon"],
        },
        "zone_id": data["zone_id"],
    }
    delivery_ref.document(data["id"]).set(delivery)
    return jsonify(delivery), 201


@app.route("/deliveries/id", methods=["GET"])
def get_deliveries_IDs():
    id = request.args.get("id")
    creator_id = request.args.get("creator_id")
    if id:
        delivery = db.collection("deliveries").document(id).get()
        if delivery.exists:
            return jsonify(delivery.to_dict()), 200
        else:
            return jsonify({"error": "Delivery not found"}), 404
    elif creator_id:
        deliveries = (
            db.collection("deliveries").where("creator_id", "==", creator_id).get()
        )
        results = []
        for delivery in deliveries:
            results.append(delivery.to_dict())
        return jsonify(results), 200
    else:
        return jsonify({"error": "Must provide an ID or creator ID parameter"}), 400


@app.route("/deliveries/pagination", methods=["GET"])
def get_deliveries_pag():
    per_page = int(request.args.get("per_page", 10))
    page = int(request.args.get("page", 1))
    start_at = (page - 1) * per_page
    end_at = start_at + per_page
    deliveries_ref = (
        db.collection("deliveries")
        .order_by("creation_date", direction=firestore.Query.DESCENDING)
        .offset(start_at)
        .limit(per_page)
    )
    deliveries = [delivery.to_dict() for delivery in deliveries_ref.stream()]
    return jsonify(deliveries), 200


@app.route("/bots", methods=["POST"])
def create_bot():
    bot = request.get_json()
    bot_ref = bots_ref.document()
    bot_id = bot_ref.id
    bot["id"] = bot_id
    bot_ref.set(bot)
    return jsonify({"id": bot_id}), 201


@app.route("/bots/<zone_id>", methods=["GET"])
def get_bots_by_zone(zone_id):
    bots = []
    query = bots_ref.where("zone_id", "==", zone_id).get()
    for doc in query:
        bots.append(doc.to_dict())
    return jsonify(bots)


@app.route("/orders/<order_id>/assign", methods=["PUT"])
def assign_bot(order_id):
    delivery_ref = db.collection("deliveries")
    bots_ref = db.collection("bots")

    order = delivery_ref.document(order_id).get().to_dict()
    if order["state"] != "pending":
        return jsonify({"message": "Order cannot be assigned."}), 400

    bots = []
    query = (
        bots_ref.where("zone_id", "==", order["zone_id"])
        .where("status", "==", "available")
        .get()
    )
    for doc in query:
        bots.append(doc)

    if not bots:
        return jsonify({"message": "No available bots."}), 400

    bot = bots[0]
    bot_ref = bots_ref.document(bot.id)
    bot_ref.update({"status": "busy"})

    delivery_ref.document(order_id).update({"bot_id": bot.id, "state": "assigned"})

    return jsonify({"message": "Bot assigned successfully."})


# @app.route("/orders/assign", methods=["PUT"])
# def assign_bot():
#     # Get all pending orders
#     delivery_ref = db.collection("deliveries")
#     orders_query = delivery_ref.where("state", "==", "pending").get()

#     for order_doc in orders_query:
#         order = order_doc.to_dict()

#         # Find available bots in the same zone as the order's pickup location
#         bots_ref = db.collection("bots")
#         bots_query = (
#             bots_ref.where("zone_id", "==", order["zone_id"])
#             .where("status", "==", "available")
#             .get()
#         )

#         if bots_query:
#             # Calculate the distance between each bot and the order's pickup location
#             bots = []
#             for bot_doc in bots_query:
#                 bot = bot_doc.to_dict()
#                 bot_distance = calculate_distance(
#                     bot["location"], order["pickup_location"]
#                 )
#                 bots.append({"bot_doc": bot_doc, "distance": bot_distance})

#             # Sort the bots by distance (from closest to farthest)
#             sorted_bots = sorted(bots, key=lambda x: x["distance"])

#             # Assign the closest available bot to the order
#             bot_doc = sorted_bots[0]["bot_doc"]
#             bot_ref = bots_ref.document(bot_doc.id)
#             bot_ref.update({"status": "busy"})
#             delivery_ref.document(order_doc.id).update(
#                 {"bot_id": bot_doc.id, "state": "assigned"}
#             )

#     return jsonify({"message": "Bots assigned successfully."})


# # Helper function to calculate the distance between two locations (in this case, represented as dictionaries with latitude and longitude keys)
# def calculate_distance(location1, location2):
#     lat1, lon1 = location1["latitude"], location1["longitude"]
#     lat2, lon2 = location2["latitude"], location2["longitude"]
#     radius = 6371  # km

#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
#         math.radians(lat1)
#     ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     distance = radius * c

#     return distance

if __name__ == "__main__":
    app.run()
