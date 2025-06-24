from flask import Flask, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import os, pytz, sshtunnel
from find_bikes import get_curr_lat_long, get_station_locations, find_three_closest, get_low_three_status, convert_to_string
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)

load_dotenv()

if os.environ.get('ENV') == 'dev':
    tunnel = sshtunnel.SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'),
        ssh_username=os.environ.get('DB_SSH_USERNAME'),
        ssh_password=os.environ.get('DB_SSH_PASSWORD'),
        remote_bind_address=(os.environ.get('DB_REMOTE_BIND_ADDRESS'), 3306))
    tunnel.start()
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWD')}@127.0.0.1:{tunnel.local_bind_port}/{os.environ.get('DB_DB')}"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWD')}@solomonrb.mysql.pythonanywhere-services.com/{os.environ.get('DB_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/sms_to_citibike',methods=['POST','GET'])
def sms_to_citibike():
    if request.method == 'POST':
        address = request.form['Body']
        number = int(request.form['From'].replace("+", ""))
        current_dt = datetime.now(pytz.timezone('America/New_York')).strftime("%Y-%m-%d %H:%M:%S")
        
        if address == "UNSUB":
            resp = MessagingResponse()
            resp.message("You have successfully opted-out!")
            return str(resp)

        target = get_curr_lat_long(address)

        if target != []:
            indexed_target = target[0]['geometry']['location']
            stations = get_station_locations()
            low_three = find_three_closest(indexed_target, stations)
            pre_string = get_low_three_status(low_three)
            converted = convert_to_string(pre_string)
        else:
            converted = "No Google Maps address found. Try cleaning up formatting like 'E 29 St and 1 Av Manhattan' or 'Houston St and Macdougal St' or 'N 7 St and Bedford Av Williamsburg' with no extra words."

        user = User.query.filter_by(phone=number).first()
        if not user:
            user = User(phone=number, text_count=0)
            db.session.add(user)
        user.text_count += 1

        event = Event(phone=number, time=current_dt, content=address, response=converted)
        db.session.add(event)
        
        db.session.commit()

        resp = MessagingResponse()
        resp.message(converted)
        return str(resp)
    else:
        return render_template('sms_to_citibike.html')
 
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.Text)
    time = db.Column(db.DateTime)
    content = db.Column(db.Text)
    response = db.Column(db.Text)

class User(db.Model):
    __tablename__ = 'users'
    phone = db.Column(db.Text, primary_key=True)
    text_count = db.Column(db.Integer)

if __name__ == "__main__":
  app.run()