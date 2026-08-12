from flask import Flask, request, jsonify
from otp import genotp
from cmail import send_mail
from stoken import entoken, dntoken
app = Flask(__name__)


@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Welcome to the APP33Ecom"}), 200


@app.route('/api/admin/registration', methods=['POST'])
def admin_create():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No input data provided"}), 400
        username = data.get('username', '').strip()
        useremail = data.get('useremail', '').strip()
        useraddress = data.get('useraddress', '').strip()
        userpassword = data.get('userpassword', '').strip()
        userphone = data.get('userphone', '').strip()
        return jsonify({"status": "success", "message": "data recieved successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"{str(e)}"}), 500


app.run(use_reloader=True, debug=True)
