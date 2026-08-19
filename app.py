from flask import Flask, request, jsonify, session
from flask_session import Session
from otp import genotp
from unqnamegen import genname
from cmail import send_mail
from stoken import entoken, dntoken
import re
from datetime import datetime, timedelta
from mysql.connector import (connection)
from flask_bcrypt import Bcrypt  # bowl fish algo
import os
from werkzeug.utils import secure_filename

# base directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # finding base_dir
# define virtual static path
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
# create folders for our virtual path
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_LENGTH_CONTENT = 10*1024*1024  # 10mb


# dbconnection
mydb = connection.MySQLConnection(user='root', password='mysql',
                                  host='localhost',
                                  database='ecommerce_cg')


app = Flask(__name__)
app.secret_key = 'ECOM345'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_LENGTH_CONTENT'] = MAX_LENGTH_CONTENT


Session(app)

bcrypt = Bcrypt(app)


@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Welcome to the APP33Ecom"}), 200


@app.route('/api/admin/registration', methods=['POST'])
def admin_create():
    cursor = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No input data provided"}), 400
        admin_username = data.get('username', '').strip()
        admin_useremail = data.get('useremail', '').strip()
        admin_useraddress = data.get('useraddress', '').strip()
        admin_userpassword = data.get('userpassword', '').strip()
        admin_userphone = data.get('userphone', '').strip()
        admin_useragree = data.get('useragree')
        if not admin_username:
            return jsonify({'status': 'failed', 'message': 'bandha ko username deserved'})
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, admin_useremail):
            return jsonify({'status': 'failed', 'message': 'bandha useremail wrong likha'})
        if len(admin_userpassword) < 6:
            return jsonify({'status': 'failed', 'message': 'password dek bhai thoda sa bhada password min 6 letters dalo'})
        # mysql connection
        mydb.ping(reconnect=True)  # to not loose connection with mysql
        # without raising error for empty set data
        cursor = mydb.cursor(buffered=True)
        hash_password = bcrypt.generate_password_hash(
            admin_userpassword).decode('utf-8')
        cursor.execute(
            'select adminid,admin_otp,otp_expiry_time,account_status from admindata where adminemail=%s', [admin_useremail])
        existed_admindata = cursor.fetchone()
        # print(existed_admindata)
        adminotp = genotp()
        otp_expiry_time = datetime.now()+timedelta(minutes=5)
        print(otp_expiry_time)
        if existed_admindata:
            if existed_admindata[3] == 'active':
                return jsonify({"status": "failed", "message": "user already existed"}), 400
            if existed_admindata[3] == 'inactive':
                cursor.execute('update admindata set adminname=%s,adminaddress=%s,adminpassword=%s,adminphone=%s,admin_otp=%s,otp_expiry_time=%s,account_status=%s,admin_agree=%s where adminemail=%s', [
                               admin_username, admin_useraddress, hash_password, admin_userphone, adminotp, otp_expiry_time, 'inactive', admin_useragree, admin_useremail])
                mydb.commit()
            else:
                return jsonify({"status": "failed", "message": "invalid account status"}), 400
        else:
            cursor.execute('insert into admindata(adminid,adminname,adminemail,adminaddress,adminpassword,adminphone,admin_otp,otp_expiry_time,account_status,admin_agree) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s,%s,%s)', [
                           admin_username, admin_useremail, admin_useraddress, hash_password, admin_userphone, adminotp, otp_expiry_time, 'inactive', admin_useragree])
            mydb.commit()

        subject = ''' Hello admin use the otp for app registration'''
        body = f'''ye lelo bhai isse kaam hogo otp dhek {adminotp}'''
        send_mail(to=admin_useremail, subject=subject, body=body)
        return jsonify({"status": "success", "message": "chal bhai iss email ko otp bhej diya bhai", "email": admin_useremail}), 200
    except Exception as e:
        mydb.rollback()
        print(e)
        return jsonify({"status": "error", "message": f"{str(e)}"}), 500


@app.route('/api/admin/verify-otp', methods=['POST'])
def adminotpverify():
    cursor = None
    try:
        data = request.get_json()
        email = data.get('email', '')
        userotp = data.get('otp')
        otp_time = datetime.now()
        if not data:
            return jsonify({'status': 'failed', "message": "No input data given"}), 400
        if not email:
            return jsonify({'status': 'failed', 'message': 'useremail required'}), 400
        if not userotp:
            return jsonify({'status': 'failed', 'message': 'OTP required'}), 400
        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)
        cursor.execute(
            'select adminid,admin_otp,otp_expiry_time,account_status from admindata where adminemail=%s', [email])
        stored_admindata = cursor.fetchone()
        print(stored_admindata)
        if not stored_admindata:
            return jsonify({"status": "failed", "message": "No user found"}), 400
        if stored_admindata[3] == 'active':
            return jsonify({"status": "failed", "message": "user Already existed"}), 400
        if otp_time > stored_admindata[2]:
            return jsonify({"status": "failed", "message": "OTP Expiried"}), 400
        if userotp != stored_admindata[1]:
            return jsonify({"status": "failed", "message": "invalid otp"}), 400
        if userotp == stored_admindata[1] and otp_time < stored_admindata[2] and stored_admindata[3] == 'inactive':
            cursor.execute(
                'update admindata set admin_otp=null,otp_expiry_time=null,account_status="active" where adminemail=%s', [email])
            mydb.commit()
        else:
            return jsonify({"status": "failed", "message": "in if block"})
        return jsonify({"status": "success", "message": "OTP verified successfully"}), 200
    except Exception as e:
        mydb.rollback()
        print(e)
        return jsonify({"status": "failed", "message": f"{str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()


@app.route('/api/admin/login', methods=['POST'])
def adminlogin():
    cursor = None
    try:
        data = request.get_json()
        login_email = data.get('email', None).strip()
        login_password = data.get('password').strip()
        if not login_email or not login_password:
            return jsonify({'status': 'failed', 'message': 'required password or email'}), 400
        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)
        cursor.execute(
            'select bin_to_uuid(adminid),adminemail,adminpassword,account_status from admindata where adminEmail=%s', [login_email])
        stored_admindata = cursor.fetchone()
        if not stored_admindata:
            return jsonify({'status': 'failed', 'message': 'No user found'}), 400
        if stored_admindata[3] == 'inactive':
            return jsonify({'status': 'failed', 'message': 'please register again'}), 400
        if not bcrypt.check_password_hash(stored_admindata[2], login_password):
            return jsonify({'status': 'failed', 'message': 'invalid password'}), 400
        session['adminid'] = stored_admindata[0]
        session['adminemail'] = stored_admindata[1]
        return jsonify({'status': 'success', 'message': 'Login successful', 'admin': {'adminid': stored_admindata[0], 'adminuser': stored_admindata[1]}}), 200
    except Exception as e:
        print(e)
        return jsonify({"status": "failed", "message": f"{str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()


@app.route('/admin/dashboard', methods=['GET'])
def admindashboard():
    if not session.get('adminid'):
        return jsonify({"status": "failed", "message": "please login first"}), 500
    return jsonify({"status": "success", "message": "Welcome to dashboard"}), 200


@app.route('/api/adminlogout', methods=['POST'])
def adminlogout():
    if not session.get('adminid'):
        return jsonify({'status': 'failed', 'message': 'please login first'}), 500
    session.pop('adminid')
    session.pop('adminemail')
    return jsonify({'status': 'success', 'message': 'logout successfull'}), 200


def allow_extension(filename: str) -> bool:
    return ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


@app.route('/api/additem', methods=['POST'])
def additem():
    cursor = None
    try:
        if not session.get('adminid'):
            return jsonify({"status": 'failed', 'message': 'please login first'}), 500
        data = request.form
        item_name = data.get('itemname', '').strip()
        if not item_name:
            return jsonify({'status': 'failed', 'message': f'item name required'}), 400
        item_description = data.get('item_desc', '').strip()
        item_about = data.get('item_about', '').strip()
        item_price = data.get('item_price').strip()
        item_quantity = data.get('item_quantity')
        try:
            item_price = float(item_price)
            item_quantity = int(item_quantity)
        except ValueError:
            return jsonify({"status": "failed", "message": f"invalid data for item quantity"}), 400

        item_category = data.get('item_category')
        item_filedata = request.files['file']
        # print(item_filedata)
        if not item_filedata:
            return jsonify({'status': 'failed', 'message': 'file data required'}), 400
        if not item_filedata.mimetype.startswith('application/octet-stream'):
            return jsonify({'status': 'failed', 'message': 'invalid file data'}), 400
        filename = item_filedata.filename
        if not allow_extension(filename):
            return jsonify({"status": "failed", "message": f"Invalid filetype extension"}), 400
        # removes unwanted data / harmful data
        safe_filename = secure_filename(filename)
        ext = os.path.splitext(safe_filename)[1]  # extracts extension
        new_filename = genname()+ext
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)  # to handle empty data
        added_by = session.get('adminid')
        cursor.execute(
            'insert into items (itemid,itemname,item_description,item_about,item_price,item_stock,item_category,item_filename,added_by) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s,uuid_to_bin(%s))', [item_name, item_description, item_about, item_price, item_quantity, item_category, new_filename, added_by])
        mydb.commit()
        if save_path:
            item_filedata.save(save_path)  # image is stored in the disk
        return jsonify({'status': 'success', 'message': 'item details successfully stored in DB'}), 200
    except Exception as e:
        mydb.rollback()
        print(e)
        return jsonify({'status': 'failed', 'message': f'{str(e)}'}), 500


app.run(use_reloader=True, debug=True)
