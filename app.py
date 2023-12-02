from flask import Flask, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import os
from flask_executor import Executor
from find_bikes import get_curr_lat_long, get_station_locations, find_three_closest, get_low_three_status, convert_to_string
from db import db_update_users, db_update_events
import pytz


app = Flask(__name__)
#to make background tasks work
app.config['EXECUTOR_TYPE'] = 'thread'
app.config['EXECUTOR_POOL_RESTARTS'] = True
executor = Executor(app)

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

        #trigger in background to speed up response
        executor.submit(db_update_users(number))
        executor.submit(db_update_events(number,current_dt,address,converted))

        resp = MessagingResponse()
        resp.message(converted)
        return str(resp)
    else:
        return render_template('sms_to_citibike.html')
 

if __name__ == "__main__":
  app.run()