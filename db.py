import MySQLdb
import sshtunnel
import os
from dotenv import load_dotenv

#to connect to DB
sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0

#to load in env variables
load_dotenv()
db_ssh_username = os.environ.get('DB_SSH_USERNAME')
db_ssh_password = os.environ.get('DB_SSH_PASSWORD')
db_remote_bind_address = os.environ.get('DB_REMOTE_BIND_ADDRESS')
db_user = os.environ.get('DB_USER')
db_passwd = os.environ.get('DB_PASSWD')
db_db = os.environ.get('DB_DB')

def db_update_users(number):
    with sshtunnel.SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'),
        ssh_username=db_ssh_username, ssh_password=db_ssh_password,
        remote_bind_address=(db_remote_bind_address, 3306)
    ) as tunnel:
        conn = MySQLdb.connect(
            user=db_user,
            passwd=db_passwd,
            host='127.0.0.1', port=tunnel.local_bind_port,
            db=db_db,
        )
        cursor = conn.cursor()

        #the piece that changes
        check_user_query = "SELECT * FROM users WHERE phone = %s"
        check_user_values = (number,)
        cursor.execute(check_user_query, check_user_values)
        existing_user = cursor.fetchone()
        if existing_user:
            curr_phone, curr_text_count = existing_user 
            user_query = "UPDATE users SET phone = %s, text_count = %s WHERE phone = %s"
            user_values = (curr_phone, curr_text_count+1, curr_phone)
        else:
            user_query = "INSERT INTO users (phone, text_count) VALUES (%s, %s)"
            user_values = (number, 1)

        cursor.execute(user_query, user_values)
        conn.commit()
        cursor.close()
        conn.close()  


def db_update_events(phone, time, content, response):
    with sshtunnel.SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'),
        ssh_username=db_ssh_username, ssh_password=db_ssh_password,
        remote_bind_address=(db_remote_bind_address, 3306)
    ) as tunnel:
        conn = MySQLdb.connect(
            user=db_user,
            passwd=db_passwd,
            host='127.0.0.1', port=tunnel.local_bind_port,
            db=db_db,
        )
        cursor = conn.cursor()

        # the piece that changes
        user_query = "INSERT INTO events (phone, time, content, response) VALUES (%s, %s, %s, %s)"
        user_values = (phone, time, content, response)

        cursor.execute(user_query, user_values)
        conn.commit()
        cursor.close()
        conn.close() 