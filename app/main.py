import unittest
import firebase_admin
import flask
import json
import uuid
import requests
import datetime

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
from flasgger import Swagger
from flasgger.utils import swag_from


from werkzeug.security import generate_password_hash
from flask_login import UserMixin, login_user

app = Flask(__name__)
bootstrap = Bootstrap(app)
CORS(app)
swagger = Swagger(app)

app.config["SECRET_KEY"] = "secret_key"

cred = credentials.Certificate("./keys.json")
firebase_admin.initialize_app(
    cred, {"databaseURL": "https://kiwibot-firebase-default-rtdb.firebaseio.com/"}
)

db = firestore.client()
delivery_ref = db.collection("deliveries")
bots_ref = db.collection("bots")

FIREBASE_WEB_API_KEY = "AIzaSyDDXoYMguAPy72k_z5Zl-4cdM_b8TbwflU"
rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


def sign_in_with_email_and_password(
    email: str, password: str, return_secure_token: bool = True
):
    payload = json.dumps(
        {"email": email, "password": password, "returnSecureToken": return_secure_token}
    )

    r = requests.post(rest_api_url, params={"key": FIREBASE_WEB_API_KEY}, data=payload)

    return r.json()


@app.route("/login_user", methods=["POST"])
@swag_from(
    {
        "summary": "Logs in a user",
        "tags": ["Users"],
        "description": "Logs in a user and returns a token",
        "parameters": [
            {
                "name": "email",
                "description": "The user's email",
                "in": "formData",
                "type": "string",
                "required": True,
            },
            {
                "name": "password",
                "description": "The user's password",
                "in": "formData",
                "type": "string",
                "required": True,
            },
        ],
        "responses": {
            "200": {
                "description": "A token representing the user's session",
                "schema": {"type": "string"},
            },
            "401": {"description": "Invalid credentials"},
        },
    }
)
def login_user():
    email = request.form.get("email")
    password = request.form.get("password")

    token = sign_in_with_email_and_password(email, password)

    return jsonify(token)


@app.route("/signup_user", methods=["POST"])
@swag_from(
    {
        "summary": "Create a new user account",
        "tags": ["Users"],
        "parameters": [
            {
                "in": "body",
                "name": "user",
                "description": "The user object",
                "schema": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "password": {"type": "string"},
                        "display_name": {"type": "string"},
                        "disabled": {"type": "boolean"},
                    },
                    "required": ["email", "password"],
                },
            }
        ],
        "responses": {
            "200": {"description": "User account created successfully"},
            "400": {"description": "Invalid request payload"},
            "500": {"description": "Internal server error"},
        },
    }
)
def create_user():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    display_name = data.get("display_name")
    disabled = data.get("disabled")

    user = auth.create_user(
        email=email,
        email_verified=False,
        password=password,
        display_name=display_name,
        disabled=disabled,
    )

    return f"Successfully created new user: {user.uid}"


class LoginForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Enviar")


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


@app.route("/login_view", methods=["GET", "POST"])
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


@app.route("/signup_view", methods=["GET", "POST"])
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


@app.route("/deliveries", methods=["POST"])
@swag_from(
    {
        "summary": "Create a new delivery",
        "tags": ["Deliveries"],
        "parameters": [
            {
                "name": "Authorization",
                "in": "header",
                "type": "string",
                "required": True,
                "description": "Bearer token for authentication",
            },
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "state": {"type": "string"},
                        "pickup": {
                            "type": "object",
                            "properties": {
                                "pickup_lat": {"type": "number"},
                                "pickup_lon": {"type": "number"},
                            },
                        },
                        "dropoff": {
                            "type": "object",
                            "properties": {
                                "dropoff_lat": {"type": "number"},
                                "dropoff_lon": {"type": "number"},
                            },
                        },
                        "zone_id": {"type": "string"},
                    },
                    "required": ["state", "pickup", "dropoff", "zone_id"],
                },
            },
        ],
        "responses": {
            "200": {
                "description": "Delivery created",
                "schema": {
                    "type": "string",
                    "example": "Delivery created with ID: a6db76a6-7bdc-431c-b14f-20251ca72fb7",
                },
            },
            "400": {"description": "Invalid pickup or dropoff location"},
            "401": {"description": "Unauthorized"},
        },
    }
)
def create_delivery():
    try:
        headers = request.headers
        bearer = headers.get("Authorization")
        token = bearer.split()[1]
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
    except:
        return "Unauthorized", 401
    data = request.json
    creation_date = datetime.datetime.now()
    state = data["state"]
    pickup_lat = data["pickup"]["pickup_lat"]
    pickup_lon = data["pickup"]["pickup_lon"]
    dropoff_lat = data["dropoff"]["dropoff_lat"]
    dropoff_lon = data["dropoff"]["dropoff_lon"]
    zone_id = data["zone_id"]

    if state not in ["pending", "assigned", "in_transit", "delivered"]:
        return "Invalid state value", 400

    if not (-90 <= pickup_lat <= 90) or not (-180 <= pickup_lon <= 180):
        return "Invalid pickup location, check your values", 400
    if not (-90 <= dropoff_lat <= 90) or not (-180 <= dropoff_lon <= 180):
        return "Invalid dropoff location, check your values", 400

    delivery_id = str(uuid.uuid4())
    delivery_creator_id = str(uuid.uuid4())

    delivery_ref = db.collection("deliveries").document(delivery_id)
    delivery_ref.set(
        {
            "id": delivery_id,
            "creation_date": creation_date,
            "state": state,
            "pickup": {"pickup_lat": pickup_lat, "pickup_lon": pickup_lon},
            "dropoff": {"dropoff_lat": dropoff_lat, "dropoff_lon": dropoff_lon},
            "zone_id": zone_id,
        }
    )

    delivery_creator_ref = db.collection("deliveries_creator").document(
        delivery_creator_id
    )
    delivery_creator_ref.set(
        {
            "delivery_id": delivery_id,
            "creator_id": uid,
        }
    )

    return f"Delivery created with ID: {delivery_id}"


@app.route("/deliveries", methods=["GET"])
@swag_from(
    {
        "summary": "Get deliveries by creator_id or id.",
        "tags": ["Deliveries"],
        "parameters": [
            {
                "in": "query",
                "name": "creator_id",
                "type": "string",
                "description": "Creator ID to filter deliveries by.",
            },
            {
                "in": "query",
                "name": "id",
                "type": "string",
                "description": "Delivery ID to retrieve.",
            },
        ],
        "responses": {
            200: {
                "description": "A list of deliveries, or a single delivery if an ID is provided.",
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "address": {"type": "string"},
                            "creator_id": {"type": "string"},
                        },
                    },
                },
            },
            400: {"description": "The request is missing a required parameter."},
            404: {
                "description": "No deliveries found for provided creator_id, or delivery not found."
            },
        },
    }
)
def get_deliveries():
    creator_id = flask.request.args.get("creator_id")

    if creator_id:
        delivery_ids = [
            doc.to_dict()["delivery_id"]
            for doc in db.collection("deliveries_creator")
            .where("creator_id", "==", creator_id)
            .stream()
        ]

        deliveries = [
            doc.to_dict()
            for doc in db.collection("deliveries")
            .where("id", "in", delivery_ids)
            .stream()
        ]

        if not deliveries:
            return (
                flask.jsonify(
                    {"message": "No deliveries found for provided creator_id."}
                ),
                404,
            )

        return flask.jsonify(deliveries)

    delivery_id = flask.request.args.get("id")
    if delivery_id:
        doc_ref = db.collection("deliveries").document(delivery_id)
        doc = doc_ref.get()
        if doc.exists:
            delivery = doc.to_dict()
            return flask.jsonify(delivery)
        else:
            return flask.jsonify({"message": "Delivery not found."}), 404

    return (
        flask.jsonify({"message": "Please provide an id or creator_id parameter."}),
        400,
    )


@app.route("/bots", methods=["POST"])
@swag_from(
    {
        "tags": ["Bots"],
        "summary": "Create a new bot.",
        "parameters": [
            {
                "name": "bot_data",
                "in": "body",
                "description": "JSON data for the new bot.",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "The current status of the bot.",
                            "enum": ["available", "busy", "reserved"],
                        },
                        "location": {
                            "type": "object",
                            "description": "The current location of the bot.",
                            "properties": {
                                "lat": {
                                    "type": "number",
                                    "format": "float",
                                    "description": "The latitude of the bot.",
                                    "minimum": -90,
                                    "maximum": 90,
                                },
                                "lon": {
                                    "type": "number",
                                    "format": "float",
                                    "description": "The longitude of the bot.",
                                    "minimum": -180,
                                    "maximum": 180,
                                },
                            },
                            "required": ["lat", "lon"],
                        },
                        "zone_id": {
                            "type": "string",
                            "description": "The ID of the zone that the bot is assigned to.",
                        },
                    },
                    "required": ["status", "location", "zone_id"],
                },
            },
        ],
        "responses": {
            "201": {
                "description": "The new bot was created successfully.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "The ID of the new bot.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The current status of the bot.",
                            "enum": ["available", "busy", "reserved"],
                        },
                        "location": {
                            "type": "object",
                            "description": "The current location of the bot.",
                            "properties": {
                                "lat": {
                                    "type": "number",
                                    "format": "float",
                                    "description": "The latitude of the bot.",
                                    "minimum": -90,
                                    "maximum": 90,
                                },
                                "lon": {
                                    "type": "number",
                                    "format": "float",
                                    "description": "The longitude of the bot.",
                                    "minimum": -180,
                                    "maximum": 180,
                                },
                            },
                            "required": ["lat", "lon"],
                        },
                        "zone_id": {
                            "type": "string",
                            "description": "The ID of the zone that the bot is assigned to.",
                        },
                    },
                    "required": ["id", "status", "location", "zone_id"],
                },
            },
            "400": {
                "description": "The latitude or longitude values in the request are invalid.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "A description of the error.",
                        },
                    },
                    "required": ["message"],
                },
            },
        },
    },
)
def create_bot():
    data = flask.request.get_json()
    if not data:
        return flask.jsonify({"message": "No data provided."}), 400

    lat = data["location"]["lat"]
    lon = data["location"]["lon"]
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        return flask.jsonify({"message": "Invalid latitude or longitude values."}), 400

    status = data["status"]
    if status not in ["available", "busy", "reserved"]:
        return flask.jsonify({"message": "Invalid status value."}), 400

    bot_id = str(uuid.uuid4())
    bot_doc = {
        "id": bot_id,
        "status": data["status"],
        "location": {"lat": data["location"]["lat"], "lon": data["location"]["lon"]},
        "zone_id": data["zone_id"],
    }

    db.collection("bots").document(bot_id).set(bot_doc)

    return flask.jsonify(bot_doc), 201


@app.route("/bots", methods=["GET"])
def get_bots():
    zone_id = flask.request.args.get("zone_id")

    bots = db.collection("bots").where("zone_id", "==", zone_id).get()

    if not bots:
        return flask.jsonify({"message": "No bots found in this zone."}), 404

    bot_list = []

    for bot in bots:
        bot_data = bot.to_dict()
        bot_data["id"] = bot.id
        bot_list.append(bot_data)

    return flask.jsonify(bot_list)


@app.route("/assign_bot", methods=["POST"])
def assign_bot():
    bot_id = request.json.get("bot_id")
    delivery_id = request.json.get("delivery_id")

    bot_ref = db.collection("bots").document(bot_id)
    bot_data = bot_ref.get().to_dict()
    if bot_data["status"] != "available":
        return jsonify({"message": "Bot is not available."}), 400

    delivery_ref = db.collection("deliveries").document(delivery_id)
    delivery_data = delivery_ref.get().to_dict()
    if delivery_data["state"] != "pending":
        return jsonify({"message": "Delivery is not in pending state."}), 400

    bot_ref.update({"status": "busy", "delivery_id": delivery_id})

    delivery_ref.update({"state": "assigned"})

    return jsonify({"message": "Bot assigned successfully."})


@app.route("/assign_bots_to_pending_deliveries", methods=["POST"])
def assign_bots_to_pending_deliveries():
    pending_deliveries = []
    deliveries_ref = db.collection("deliveries")
    query = deliveries_ref.where("state", "==", "pending").get()
    for doc in query:
        delivery_data = doc.to_dict()
        delivery_data["id"] = doc.id
        pending_deliveries.append(delivery_data)

    available_bots = []
    bots_ref = db.collection("bots")
    query = bots_ref.where("status", "==", "available").get()
    for doc in query:
        bot_data = doc.to_dict()
        bot_data["id"] = doc.id
        available_bots.append(bot_data)

    for delivery in pending_deliveries:
        assigned_bot = None
        min_distance = float("inf")
        for bot in available_bots:
            bot_zone_id = bot["zone_id"]
            delivery_zone_id = delivery["zone_id"]
            if bot_zone_id == delivery_zone_id:
                bot_location = (bot["location"]["lat"], bot["location"]["lon"])
                delivery_location = (
                    delivery["pickup"]["pickup_lat"],
                    delivery["pickup"]["pickup_lon"],
                )
                bot_distance_to_delivery = distance(bot_location, delivery_location).km
                if bot_distance_to_delivery < min_distance:
                    assigned_bot = bot
                    min_distance = bot_distance_to_delivery

        if assigned_bot is not None:
            bot_ref = db.collection("bots").document(assigned_bot["id"])
            bot_ref.update({"status": "busy", "delivery_id": delivery["id"]})

            delivery_ref = db.collection("deliveries").document(delivery["id"])
            delivery_ref.update({"state": "assigned"})

            available_bots.remove(assigned_bot)

    return jsonify({"message": "Bots assigned to pending deliveries successfully."})


if __name__ == "__main__":
    app.run()
