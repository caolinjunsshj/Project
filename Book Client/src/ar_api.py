# NOTE: this is not the actual API file for the author-reader project. Use only for reference.

#To run program:  python3 fth_api.py prashant

#README:  if conn error make sure password is set properly in RDS PASSWORD section

#README:  Debug Mode may need to be set to Fales when deploying live (although it seems to be working through Zappa)

#README:  if there are errors, make sure you have all requirements are loaded
#pip3 install flask
#pip3 install flask_restful
#pip3 install flask_cors
#pip3 install Werkzeug
#pip3 install pymysql
#pip3 install python-dateutil

import os
import uuid
import boto3
import json
import math
from datetime import datetime
from datetime import timedelta
from pytz import timezone
import random
import string
import stripe

from flask import Flask, request, render_template
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_mail import Mail, Message
# used for serializer email and error handling
#from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
#from flask_cors import CORS

from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.security import generate_password_hash, \
     check_password_hash


#  NEED TO SOLVE THIS
# from NotificationHub import Notification
# from NotificationHub import NotificationHub
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from dateutil.relativedelta import *
from decimal import Decimal
from datetime import datetime, date, timedelta
from hashlib import sha512
from math import ceil
import string
import random
# BING API KEY
# Import Bing API key into bing_api_key.py

#  NEED TO SOLVE THIS
# from env_keys import BING_API_KEY, RDS_PW

import decimal
import sys
import json
import pytz
import pymysql
import requests

#RDS_HOST = 'pm-mysqldb.cxjnrciilyjq.us-west-1.rds.amazonaws.com'
RDS_HOST = 'io-mysqldb8.cxjnrciilyjq.us-west-1.rds.amazonaws.com'
#RDS_HOST = 'localhost'
RDS_PORT = 3306
#RDS_USER = 'root'
RDS_USER = 'admin'
#RDS_DB = 'feed_the_hungry'
RDS_DB = 'sf'

#app = Flask(__name__)
app = Flask(__name__, template_folder='assets')

# --------------- Stripe Variables ------------------
# these key are using for testing. Customer should use their stripe account's keys instead
import stripe
stripe_public_key = 'pk_test_6RSoSd9tJgB2fN2hGkEDHCXp00MQdrK3Tw'
stripe_secret_key = 'sk_test_fe99fW2owhFEGTACgW3qaykd006gHUwj1j'

#this is a testing key using ptydtesting's stripe account.
# stripe_public_key = "pk_test_51H0sExEDOlfePYdd9TVlnhVDOCmmnmdxAxyAmgW4x7OI0CR7tTrGE2AyrTk8VjftoigEOhv2RTUv5F8yJrfp4jWQ00Q6KGXDHV"
# stripe_secret_key = "sk_test_51H0sExEDOlfePYdd9UQDxfp8yoY7On272hCR9ti12WSNbIGTysaJI8K2W8NhCKqdBOEhiNj4vFOtQu6goliov8vF00cvqfWG6d"

stripe.api_key = stripe_secret_key
# Allow cross-origin resource sharing
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

app.config['MAIL_USERNAME'] = os.environ.get('EMAIL')
app.config['MAIL_PASSWORD'] = os.environ.get('PASSWORD')
# app.config['MAIL_USERNAME'] = ''
# app.config['MAIL_PASSWORD'] = ''

# Setting for mydomain.com
app.config['MAIL_SERVER'] = 'smtp.mydomain.com'
app.config['MAIL_PORT'] = 465

# Setting for gmail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465

app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Set this to false when deploying to live application
#app.config['DEBUG'] = True
app.config['DEBUG'] = False

app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY')

mail = Mail(app)

# API
api = Api(app)

# convert to UTC time zone when testing in local time zone
utc = pytz.utc
def getToday(): return datetime.strftime(datetime.now(utc), "%Y-%m-%d")
def getNow(): return datetime.strftime(datetime.now(utc),"%Y-%m-%d %H:%M:%S")

# Get RDS password from command line argument
def RdsPw():
    if len(sys.argv) == 2:
        return str(sys.argv[1])
    return ""

# RDS PASSWORD
# When deploying to Zappa, set RDS_PW equal to the password as a string
# When pushing to GitHub, set RDS_PW equal to RdsPw()
RDS_PW = 'prashant'
# RDS_PW = RdsPw()


s3 = boto3.client('s3')

# aws s3 bucket where the image is stored
# BUCKET_NAME = os.environ.get('MEAL_IMAGES_BUCKET')
BUCKET_NAME = 'servingnow'
# allowed extensions for uploading a profile photo file
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])



getToday = lambda: datetime.strftime(date.today(), "%Y-%m-%d")
getNow = lambda: datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")

# For Push notification
isDebug = False
NOTIFICATION_HUB_KEY = os.environ.get('NOTIFICATION_HUB_KEY')
NOTIFICATION_HUB_NAME = os.environ.get('NOTIFICATION_HUB_NAME')

# Connect to MySQL database (API v2)
def connect():
    global RDS_PW
    global RDS_HOST
    global RDS_PORT
    global RDS_USER
    global RDS_DB

    print("Trying to connect to RDS (API v2)...")
    try:
        conn = pymysql.connect( RDS_HOST,
                                user=RDS_USER,
                                port=RDS_PORT,
                                passwd=RDS_PW,
                                db=RDS_DB,
                                cursorclass=pymysql.cursors.DictCursor)
        print("Successfully connected to RDS. (API v2)")
        return conn
    except:
        print("Could not connect to RDS. (API v2)")
        raise Exception("RDS Connection failed. (API v2)")

# Disconnect from MySQL database (API v2)
def disconnect(conn):
    try:
        conn.close()
        print("Successfully disconnected from MySQL database. (API v2)")
    except:
        print("Could not properly disconnect from MySQL database. (API v2)")
        raise Exception("Failure disconnecting from MySQL database. (API v2)")

# Serialize JSON
def serializeResponse(response):
    try:
        print("In Serialize JSON")
        for row in response:
            for key in row:
                if type(row[key]) is Decimal:
                    row[key] = float(row[key])
                elif type(row[key]) is date or type(row[key]) is datetime:
                    row[key] = row[key].strftime("%Y-%m-%d")
        print("In Serialize JSON response", response)
        return response
    except:
        raise Exception("Bad query JSON")








# Execute an SQL command (API v2)
# Set cmd parameter to 'get' or 'post'
# Set conn parameter to connection object
# OPTIONAL: Set skipSerialization to True to skip default JSON response serialization
def execute(sql, cmd, conn, skipSerialization = False):
    response = {}
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cmd == 'get':
                result = cur.fetchall()
                response['message'] = 'Successfully executed SQL query.'
                # Return status code of 280 for successful GET request
                response['code'] = 280
                if not skipSerialization:
                    result = serializeResponse(result)
                response['result'] = result
            elif cmd in 'post':
                conn.commit()
                response['message'] = 'Successfully committed SQL command.'
                # Return status code of 281 for successful POST request
                response['code'] = 281
            else:
                response['message'] = 'Request failed. Unknown or ambiguous instruction given for MySQL command.'
                # Return status code of 480 for unknown HTTP method
                response['code'] = 480
    except:
        response['message'] = 'Request failed, could not execute MySQL command.'
        # Return status code of 490 for unsuccessful HTTP request
        response['code'] = 490
    finally:
        response['sql'] = sql
        return response

# Close RDS connection
def closeRdsConn(cur, conn):
    try:
        cur.close()
        conn.close()
        print("Successfully closed RDS connection.")
    except:
        print("Could not close RDS connection.")

# Runs a select query with the SQL query string and pymysql cursor as arguments
# Returns a list of Python tuples
def runSelectQuery(query, cur):
    try:
        cur.execute(query)
        queriedData = cur.fetchall()
        return queriedData
    except:
        raise Exception("Could not run select query and/or return data")


# ===========================================================
# Additional Helper Functions from sf_api.py
# Need to revisit to see if we need these

def helper_upload_meal_img(file, bucket, key):
    if file and allowed_file(file.filename):
        filename = 'https://s3-us-west-1.amazonaws.com/' \
                   + str(bucket) + '/' + str(key)
       
        upload_file = s3.put_object(
                            Bucket=bucket,
                            Body=file,
                            Key=key,
                            ACL='public-read',
                            ContentType='image/jpeg'
                        )
        return filename
    return None

def helper_upload_refund_img(file, bucket, key):
    print("Bucket = ", bucket)
    print("Key = ", key)
    if file:
        filename = 'https://s3-us-west-1.amazonaws.com/' \
                   + str(bucket) + '/' + str(key)
        #print('bucket:{}'.format(bucket))
        upload_file = s3.put_object(
                            Bucket=bucket,
                            Body=file,
                            Key=key,
                            ACL='public-read',
                            ContentType='image/png'
                        )
        return filename
    return None

def allowed_file(filename):
    """Checks if the file is allowed to upload"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def kitchenExists(kitchen_id):
    # scan to check if the kitchen name exists
    kitchen = db.scan(TableName='kitchens',
        FilterExpression='kitchen_id = :val',
        ExpressionAttributeValues={
            ':val': {'S': kitchen_id}
        }
    )

    return not kitchen.get('Items') == []

def couponExists(coupon_id):
    # scan to check if the kitchen name exists
    coupon = db.scan(TableName='coupons',
        FilterExpression='coupon_id = :val',
        ExpressionAttributeValues={
            ':val': {'S': coupon_id}
        }
    )

    return not coupon.get('Items') == []


# ===========================================================



















# -- Queries start here -------------------------------------------------------------------------------


# Queries for Untitled Books

class AllBooks(Resource):
    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.books;
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllBooks query successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

# Example route for API test: http://127.0.0.1:4000/api/v2/BooksByAuthorEmail/pmarathay@gmail.com
class BooksByAuthorEmail(Resource):
    def get(self, user_email):
        response = {}
        items = {}
        #data = request.get_json(force=True)
        print("User Email = ",  user_email)
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.books b
                LEFT JOIN ar.users u1
                ON b.author_uid = u1.user_uid
                LEFT JOIN ar.reviews r
                ON b.book_uid = r.rev_book_uid
                LEFT JOIN ar.users u2
                ON r.reader_id = u2.user_uid
                WHERE u1.email = \'""" + user_email + """\';
                """
            items = execute(query, 'get', conn)

            response['message'] = 'BooksByAuthorEmail query successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

# Example route for API test: http://127.0.0.1:4000/api/v2/BooksByAuthorUID/100-000001
class BooksByAuthorUID(Resource):
    def get(self, author_uid):
        response = {}
        items = {}
        print("author_uid", author_uid)
        try:
            conn = connect()
            query = """
                    SELECT * FROM ar.books 
                    WHERE author_uid = \'""" + author_uid + """\';
                    """
            items = execute(query, 'get', conn)

            response['message'] = 'BooksByAuthorUID query successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)


# Just returns the entire users table
class AllUsers(Resource):

    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.users;
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllUsers query successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

class AllAuthors(Resource):

    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.users
                WHERE role = "author";
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllAuthors query successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

class AllReaders(Resource):

    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ 
                SELECT * FROM ar.users
                WHERE role = "reader";
                """
            items = execute(query, 'get', conn)

            response['message'] = 'AllReaders query successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

# Reviews, get method tbd but for now it returns review by book
# Post adds a review
class Reviews(Resource):
    def get(self, rev_book_uid):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """
                    SELECT * FROM ar.reviews
                    WHERE rev_book_uid = \'""" + rev_book_uid + """\'
                    """
            items = execute(query, 'get', conn)

            response['message'] = 'Reviews get successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

        # http://localhost:4000/api/v2/couponDetails/Jane6364
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/couponDetails/Jane6364

# TODO 
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)

            reader_id = data['reader_id']
            num_used = (data['num_used'])
            print("reader_id", reader_id)

            query = '''
                    INSERT INTO ar.reviews
                    SET num_used = \'''' + str(num_used) + '''\'
                    WHERE coupon_uid = \'''' + str(coupon_uid) + '''\';
                    '''
            items = execute(query,'post',conn)

            response['message'] = 'CouponDetails POST successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Q3 POST Request failed, please try again later.')
        finally:
            disconnect(conn)



class UpdateFavoritesParam(Resource):
    # QUERY 4 UPDATE A SPECIFIC BUSINESS PARAMETER
    def post(self, business_type):
            response = {}
            items = []
            print("favorites", favorites)
            try:
                conn = connect()
                query = """
                        UPDATE ar.users
                        SET favorites = \'""" + favorites + """\'
                        WHERE user_uid = '100-000001';
                        """
                items = execute(query, 'post', conn)


                items['message'] = 'Favorites info updated'
                items['code'] = 200
                return items
            except:
                print("Error happened while updating users table")
                raise BadRequest('Request failed, please try again later.')
            finally:
                disconnect(conn)
                print('process completed')


class UpdateFavoritesParamJSON(Resource):

    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            user_uid = data['business_uid']
            favorites = data['favorites']
            print("user_uid", user_uid)
            print("favorites", favorites)

            query = """
                    UPDATE ar.users
                    SET favorites = \'""" + favorites + """\'
                    WHERE user_uid = \'""" + user_uid + """\';
                    """
            items = execute(query, 'post', conn)

            response['message'] = 'JSON POST successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('JSON POST Request failed, please try again later.')
        finally:
            disconnect(conn)
#----------------------------------------------------------------------------------







# Old stuff to be used for reference ----------------------------------------------



        # http://localhost:4000/api/v2/itemsByBusiness/200-000003
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/itemsByBusiness/200-000003

# QUERY 1  BUSINESSES
class Businesses(Resource):
    # QUERY 1 RETURNS ALL BUSINESSES
    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """ # QUERY 1 RETURNS ALL BUSINESSES
                SELECT * FROM sf.businesses; """
            items = execute(query, 'get', conn)

            response['message'] = 'Businesses successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)


    # # QUERY 1A UPDATES A SPECIFIC FIELD IN A SPECIFIC BUSINESSES
    # def post(self):
    #     response = {}
    #     items = {}
    #     try:
    #         conn = connect()
    #         data = request.get_json(force=True)
    #         BusinessId = data['business_id']
    #         updatedBusinessName = data['business_name']
    #         query =  '''
    #                 UPDATE  sf.businesses
    #                 SET business_name = \'''' + updatedBusinessName + '''\'
    #                 WHERE business_id = \'''' + BusinessId + '''\';
    #                 '''
    #         items = execute(query,'post',conn)

    #         response['message'] = 'Businesses Post successful'
    #         response['result'] = items
    #         return response, 200
    #     except:
    #         raise BadRequest('Q1A Request failed, please try again later.')
    #     finally:
    #         disconnect(conn)

    #     # ENDPOINT AND JSON OBJECT THAT WORKS
    #     # http://localhost:4000/api/v2/businesses
    #     # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/businesses
    #     # {"business_id":"200-000001",
    #     #  "business_name":"Infinite Options"}


    # QUERY 1B UPDATES A SPECIFIC JSON FIELD IN A SPECIFIC BUSINESSES
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            BusinessId = data['business_id']
            updatedAcceptingHours = data['business_accepting_hours']
            print("updatedAcceptingHours= ",  updatedAcceptingHours)
            query =  '''
                    UPDATE  sf.businesses
                    SET business_accepting_hours = \'''' + updatedAcceptingHours + '''\'
                    WHERE author_uid = \'''' + BusinessId + '''\';
                    '''
            items = execute(query,'post',conn)

            response['message'] = 'Businesses Post successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Q1A Request failed, please try again later.')
        finally:
            disconnect(conn)

        # ENDPOINT AND JSON OBJECT THAT WORKS
        # http://localhost:4000/api/v2/businesses
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/businesses
        # {"business_id":"200-000001",
        #  "business_accepting_hours":
        #  "{\"Monday\":\"11:00am-12:00pm\",\"Tuesday\":\"10:00am-12:00pm\",\"Wednesday\":\"10:00am-12:00pm\",\"Thursday\":\"10:00am-12:00pm\",\"Friday\":\"10:00am-12:00pm\",\"Saturday\":\"10:00am-12:00pm\",\"Sunday\":\"10:00am-12:00pm\"}"}



    

# CUSTOMER QUERY 2
class ItemsbyBusiness(Resource):
    # RETURNS ALL ITEMS FOR A SPECIFIC BUSINESS
    def get(self, author_uid):
        response = {}
        items = {}
        print("author_uid", author_uid)
        try:
            conn = connect()
            query = """
                    SELECT * FROM sf.items 
                    WHERE itm_author_uid = \'""" + author_uid + """\'
                    """
            items = execute(query, 'get', conn)

            response['message'] = 'ItemsbyBusiness successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)
        
        # http://localhost:4000/api/v2/itemsByBusiness/200-000003
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/itemsByBusiness/200-000003


# QUERY 2A
class SubscriptionsbyBusiness(Resource):
    # RETURNS ALL SUBSCRIPTION ITEMS FOR A SPECIFIC BUSINESS
    def get(self, business_id):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """
                    SELECT * FROM sf.subscription_items
                    WHERE itm_business_id = \'""" + business_id + """\'
                    """
            items = execute(query, 'get', conn)

            response['message'] = 'SubscriptionsbyBusiness successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)
        
        # http://localhost:4000/api/v2/subscriptionsByBusiness/200-000001
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/subscriptionsByBusiness/200-000001



# -- 3.  GET Query using a argument to pass in a parameter
# -- include parameter in request.args
class OneUserArg(Resource):

    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()
            user_uid = request.args['user_uid']

            query = """ # Returns request from 
                SELECT * FROM ar.users 
                WHERE user_uid = \'""" + user_uid + """\';
                """
                
            items = execute(query, 'get', conn)

            response['message'] = 'GET OneUserArg successful'
            response['result'] = items['result']
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)
        
        # ENDPOINT AND JSON OBJECT THAT WORKS
        # http://localhost:4000/api/v2/onebusinessarg?business_uid=200-000001
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/onebusinessarg?business_uid=200-000001



# QUERY 3A
# RETURNS ALL COUPON DETAILS FOR A SPECIFIC COUPON
class CouponDetails(Resource):
    def get(self, coupon_id):
        response = {}
        items = {}
        try:
            conn = connect()
            query = """
                    SELECT * FROM sf.coupons
                    WHERE coupon_id = \'""" + coupon_id + """\'
                    """
            items = execute(query, 'get', conn)

            response['message'] = 'CouponDetails successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

        # http://localhost:4000/api/v2/couponDetails/Jane6364
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/couponDetails/Jane6364


    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)

            coupon_uid = data['coupon_uid']
            num_used = (data['num_used'])
            print("coupon_uid", coupon_uid)
            print("num_used",  num_used)

            

            query = '''
                    UPDATE sf.coupons
                    SET num_used = \'''' + str(num_used) + '''\'
                    WHERE coupon_uid = \'''' + str(coupon_uid) + '''\';
                    '''
            items = execute(query,'post',conn)

            response['message'] = 'CouponDetails POST successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Q3 POST Request failed, please try again later.')
        finally:
            disconnect(conn)



# QUERY 4 
# WRITES REFUND INFO TO DB
class RefundDetails(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            # print to Received data to Terminal 
            print("Received:", data)

            email = data['email_id']
            phone = data['phone_num']
            image = data['image_url']
            note = data['customer_note']
            print('email:', email)
            print('phone_num:', phone)
            print('image_url:', image)
            print('note:', note)


            # Query [0]  Get New Refund UID
            query = ["CALL new_refund_uid;"]
            NewIDresponse = execute(query[0], 'get', conn)
            NewID = NewIDresponse['result'][0]['new_id']
            # print("NewID = ", NewID)  NewID is an Array and new_id is the first element in that array
            print("NewRefundID = ", NewID)

            TimeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("TimeStamp = ", TimeStamp)

            #Query [1]  Main Query to Insert Data Into Table
            query =  '''
                    INSERT INTO  sf.refunds
                    SET refund_uid = \'''' + NewID + '''\',
                        created_at = \'''' + TimeStamp + '''\',
                        email_id = \'''' + email + '''\',
	                    phone_num = \'''' + phone + '''\',
	                    image_url = \'''' + image + '''\',
	                    customer_note = \'''' + note + '''\';
                    '''
            items = execute(query,'post',conn)

            response['message'] = 'RefundDetails Post successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

        # ENDPOINT AND JSON OBJECT THAT WORKS
        # http://localhost:4000/api/v2/refundDetails
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/refundDetails
            # {"email_id":"wmarathay@gmail.com",
            #  "phone_num":"408-476-0001",
            #  "image_url":"http://servingnow.me",
            #  "customer_note":"Please Refund"}




# QUERY 4 REWRITE TO MATCH HOWARD'S OUTPUT
# WRITES REFUND INFO TO DB
class RefundDetailsNEW(Resource):
    def post(self):
        response = {}
        items = {}

        try:
            conn = connect()
            client_email = request.form.get('client_email')
            client_message = request.form.get('client_message')
            client_phone = request.form.get('client_phone')
            # data = request.get_json(force=True)
            # print to Received data to Terminal 
            # print("Received:", data)

            # email = data['client_email']
            # phone = data['phone_num']
            # image = data['image_url']
            # note = data['client_message']
            print('email:', client_email)
            # print('phone_num:', phone)
            # print('image_url:', image)
            print('note:', client_message)
            print('phone:', client_phone)


            # Query [0]  Get New Refund UID
            query = ["CALL new_refund_uid;"]
            NewIDresponse = execute(query[0], 'get', conn)
            NewID = NewIDresponse['result'][0]['new_id']
            # print("NewID = ", NewID)  NewID is an Array and new_id is the first element in that array
            print("NewRefundID = ", NewID)

            photo_key = 'refund_imgs/{}'.format(NewID)
            print("Photo Key = ", photo_key)
                
            print("Photo = ", photo)
            photo_path = helper_upload_refund_img(photo, BUCKET_NAME, photo_key)
            print("Photo Path = ", photo_path)



            TimeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("TimeStamp = ", TimeStamp)

            #Query [1]  Main Query to Insert Data Into Table
            query =  '''
                    INSERT INTO  sf.refunds
                    SET refund_uid = \'''' + NewID + '''\',
                        created_at = \'''' + TimeStamp + '''\',
                        email_id = \'''' + client_email + '''\',
	                    phone_num = \'''' + client_phone + '''\',
	                    image_url = \'''' + photo_path + '''\',
	                    customer_note = \'''' + client_message + '''\';
                    '''
            items = execute(query,'post',conn)

            response['message'] = 'RefundDetails Post successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)




# QUERY 8 
# WRITES PURCHASE INFO TO PURCHASES AND PAYMENTS TABLES
class PurchaseData(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            # print to Received data to Terminal 
            print("Received:", data)

            customer_uid = data['customer_uid']
            author_uid = data['author_uid']
            delivery_first_name = data['delivery_first_name']
            delivery_last_name = data['delivery_last_name']
            delivery_email = data['delivery_email']
            delivery_phone = data['delivery_phone']
            delivery_address = data['delivery_address']
            delivery_unit = data['delivery_unit']
            delivery_city = data['delivery_city']
            delivery_state = data['delivery_state']
            delivery_zip = data['delivery_zip']
            delivery_instructions = data['delivery_instructions']
            delivery_longitude = data['delivery_longitude']
            delivery_latitude = data['delivery_latitude']
            items = data['items']
            order_instructions = data['order_instructions']
            purchase_notes = data['purchase_notes']
            amount_due =  data['amount_due']
            amount_discount = data['amount_discount']
            amount_paid = data['amount_paid']

            print("customer_uid:", customer_uid)
            print("author_uid:", author_uid)

            print (author_uid )
            print (customer_uid )
            print (delivery_first_name )
            print (delivery_last_name )
            print (delivery_email )
            print (delivery_phone )
            print (delivery_address )
            print (delivery_unit )
            print (delivery_city )
            print (delivery_state )
            print (delivery_zip )
            print (delivery_instructions )
            print (delivery_longitude )
            print (delivery_latitude )
            print (items )
            print (order_instructions )
            print (purchase_notes )
            print (amount_due )
            print (amount_discount )
            print (amount_paid )

            # Query [0]  Get New Purchase UID
            query = ["CALL new_purchase_uid;"]
            NewPurIDresponse = execute(query[0], 'get', conn)
            NewPurID = NewPurIDresponse['result'][0]['new_id']
            print("NewPurID:", NewPurID)

            # Query [1]  Get New PaymentUID
            query = ["CALL new_payment_uid;"]
            NewPayIDresponse = execute(query[0], 'get', conn)
            NewPayID = NewPayIDresponse['result'][0]['new_id']
            print("NewPayID:", NewPayID)
            # print("NewID = ", NewID)  NewID is an Array and new_id is the first element in that array

            TimeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            DateStamp = datetime.now().strftime("%Y-%m-%d")
            print("TimeStamp:", TimeStamp)
            print("DateStamp:", DateStamp)

            # Query [2]  Main Query to Insert in Purchases Table
            query = '''
                    INSERT INTO  sf.purchases
                    SET purchase_uid = \'''' + NewPurID + '''\',
                        purchase_date = \'''' + TimeStamp + '''\',
                        purchase_id = \'''' + NewPurID + '''\',
                        pur_customer_uid = \'''' + customer_uid + '''\',
                        pur_author_uid = \'''' + author_uid + '''\',
                        delivery_first_name = \'''' + delivery_first_name + '''\',
                        delivery_last_name = \'''' + delivery_last_name + '''\',
                        delivery_email = \'''' + delivery_email + '''\',
                        delivery_phone_num = \'''' + delivery_phone + '''\',
                        delivery_address = \'''' + delivery_address + '''\',
                        delivery_unit = \'''' + delivery_unit + '''\',
                        delivery_city = \'''' + delivery_city + '''\',
                        delivery_state = \'''' + delivery_state + '''\',
                        delivery_zip = \'''' + delivery_zip + '''\',
                        delivery_instructions = \'''' + delivery_instructions + '''\',
                        delivery_longitude = \'''' + delivery_longitude + '''\',
                        delivery_latitude = \'''' + delivery_latitude + '''\',
                        items = \'''' + items + '''\',
                        order_instructions = \'''' + order_instructions + '''\',
                        purchase_notes = \'''' + purchase_notes + '''\';
                    '''

            items = execute(query,'post',conn)
            response['message'] = 'Purchase Data Post successful'

            # Query [3]  Main Query to Insert PaymentsTable
            query = '''
                    INSERT INTO sf.payments
                    SET payment_uid = \'''' + NewPayID + '''\',
                        payment_time_stamp = \'''' + TimeStamp + '''\',
                        payment_id = \'''' + NewPayID + '''\',
                        pay_purchase_id = \'''' + NewPurID + '''\',
                        amount_due = \'''' + amount_due + '''\',
                        amount_discount = \'''' + amount_discount+ '''\',
                        amount_paid = \'''' + amount_paid + '''\';
                        '''


            items = execute(query,'post',conn)
            response['message'] = 'Payment Data Post successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

        # ENDPOINT AND JSON OBJECT THAT WORKS
        # http://localhost:4000/api/v2/purchaseData
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/purchaseData
        # {  "customer_id":"4158329643",
        #    "business_id":"200-000003",
        #    "delivery_first_name":"Carlos",
        #    "delivery_last_name":"Torres",
        #    "delivery_email":"omarfacio2010@gmail.com",
        #    "delivery_phone":"4158329643",
        #    "delivery_address":"1658 Sacramento Street",
        #    "delivery_unit":"9",
        #    "delivery_city":"San Francisco",
        #    "delivery_state":"CA",
        #    "delivery_zip":"94109",
        #    "delivery_instructions":"Please dial 3434 to open the gate",
        #    "delivery_longitude":"37.000000",
        #    "delivery_latitude":"120.000000",
        #    "items":"{\"cilantro\": \"2\", \"potato\": \"4\", \"apple\": \"5\", \"melon\": \"1\", \"carrot\": \"2\"}",
        #    "order_instructions":"Please take care with my apples",
        #    "purchase_notes":"Repeat this order every Monday"
        # }



# QUERY 9 - QUANG'S QUERY
# PTYD WRITES PURCHASE INFO TO PURCHASES AND PAYMENTS TABLES
class MSPurchaseData(Resource):
    def post(self):
        response = {}
        items = {}
        try:
            conn = connect()
            data = request.get_json(force=True)
            # print to Received data to Terminal 
            print("Received:", data)

            customer_id = data['customer_id']
            business_id = data['business_id']
            delivery_first_name = data['delivery_first_name']
            delivery_last_name = data['delivery_last_name']
            delivery_email = data['delivery_email']
            delivery_phone = data['delivery_phone']
            delivery_address = data['delivery_address']
            delivery_unit = data['delivery_unit']
            delivery_city = data['delivery_city']
            delivery_state = data['delivery_state']
            delivery_zip = data['delivery_zip']
            delivery_instructions = data['delivery_instructions']
            delivery_longitude = data['delivery_longitude']
            delivery_latitude = data['delivery_latitude']
            items = data['items']
            order_instructions = data['order_instructions']
            purchase_notes = data['purchase_notes']
            amount_due =  data['amount_due']
            amount_discount = data['amount_discount']
            amount_paid = data['amount_paid']



            password_salt = data['salt']
            cc_num = data['cc_num']
            cc_exp_date = data['cc_exp_date']
            cc_cvv = data['cc_cvv'] 
            cc_zip = data['billing_zip'] 

            print("customer_id:", customer_id)
            print("business_id:", business_id)

            print (business_id )
            print (customer_id )
            print (delivery_first_name )
            print (delivery_last_name )
            print (delivery_email )
            print (delivery_phone )
            print (delivery_address )
            print (delivery_unit )
            print (delivery_city )
            print (delivery_state )
            print (delivery_zip )
            print (delivery_instructions )
            print (delivery_longitude )
            print (delivery_latitude )
            print (items )
            print (order_instructions )
            print (purchase_notes )
            print (amount_due )
            print (amount_discount )
            print (amount_paid )
            print (cc_num)
            print (cc_exp_date)
            print (cc_cvv)
            print (cc_zip)

            # Query [0]  Get New Purchase UID
            query = ["CALL new_purchase_uid;"]
            NewPurIDresponse = execute(query[0], 'get', conn)
            NewPurID = NewPurIDresponse['result'][0]['new_id']
            print("NewPurID:", NewPurID)

            # Query [1]  Get New PaymentUID
            query = ["CALL new_payment_uid;"]
            NewPayIDresponse = execute(query[0], 'get', conn)
            NewPayID = NewPayIDresponse['result'][0]['new_id']
            print("NewPayID:", NewPayID)
            # print("NewID = ", NewID)  NewID is an Array and new_id is the first element in that array

            TimeStamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            DateStamp = datetime.now().strftime("%Y-%m-%d")
            print("TimeStamp:", TimeStamp)
            print("DateStamp:", DateStamp)

            # Query [2]  Main Query to Insert in Purchases Table
            query = '''
                    INSERT INTO  sf.purchases
                    SET purchase_uid = new_purchase_id(),
                        purchase_date = \'''' + DateStamp + '''\',
                        purchase_id = \'''' + NewPurID + '''\',
                        customer_id = \'''' + customer_id + '''\',
                        business_id = \'''' + business_id + '''\',
                        delivery_first_name = \'''' + delivery_first_name + '''\',
                        delivery_last_name = \'''' + delivery_last_name + '''\',
                        delivery_email = \'''' + delivery_email + '''\',
                        delivery_phone_num = \'''' + delivery_phone + '''\',
                        delivery_address = \'''' + delivery_address + '''\',
                        delivery_unit = \'''' + delivery_unit + '''\',
                        delivery_city = \'''' + delivery_city + '''\',
                        delivery_state = \'''' + delivery_state + '''\',
                        delivery_zip = \'''' + delivery_zip + '''\',
                        delivery_instructions = \'''' + delivery_instructions + '''\',
                        delivery_longitude = \'''' + delivery_longitude + '''\',
                        delivery_latitude = \'''' + delivery_latitude + '''\',
                        items = \'''' + items + '''\',
                        order_instructions = \'''' + order_instructions + '''\',
                        purchase_notes = \'''' + purchase_notes + '''\';
                    '''

            items = execute(query,'post',conn)
            response['message'] = 'Purchase Data Post successful'

            # Query [3]  Main Query to Insert PaymentsTable
            query = '''
                    INSERT INTO sf.payments
                    SET payment_uid = \'''' + NewPayID + '''\',
                        payment_time_stamp = \'''' + TimeStamp + '''\',
                        payment_id = \'''' + NewPayID + '''\',
                        purchase_id = \'''' + NewPurID + '''\',
                        amount_due = \'''' + amount_due + '''\',
                        amount_discount = \'''' + amount_discount+ '''\',
                        amount_paid = \'''' + amount_paid + '''\',
                        cc_num = \'''' + cc_num + '''\', 
                        cc_exp_date = \'''' + cc_exp_date + '''\', 
                        cc_cvv = \'''' + cc_cvv + '''\', 
                        cc_zip = \'''' + cc_zip + '''\'
                        '''

            items = execute(query,'post',conn)
            response['message'] = 'Payment Data Post successful'
            response['result'] = items
            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

        # ENDPOINT AND JSON OBJECT THAT WORKS
        # http://localhost:4000/api/v2/MSpurchaseData
        # https://tsx3rnuidi.execute-api.us-west-1.amazonaws.com/dev/api/v2/MSpurchaseData
        #    {"customer_id":"100-000001",
        #     "business_id": "200-000001",
        #     "items": "320-000006",
        #     "amount_due" : "390.00",
        #     "salt": "64a7f1fb0df93d8f5b9df14077948afa1b75b4c5028d58326fb801d825c9cd24412f88c8b121c50ad5c62073c75d69f14557255da1a21e24b9183bc584efef71",
        #     "delivery_first_name":"Prashant",
        #     "delivery_last_name":"Marathay",
        #     "delivery_email":"pmarathay@gmail.com",
        #     "delivery_phone":"4084760001",
        #     "delivery_address":"6123 Corte De La Reina",
        #     "delivery_unit":"",
        #     "delivery_city":"San Jose",
        #     "delivery_state":"CA",
        #     "delivery_zip":"95120",
        #     "delivery_instructions":"Big Dog",
        #     "delivery_longitude":"-121.8891617",
        #     "delivery_latitude":",37.2271302",
        #     "order_instructions":"none",
        #     "purchase_notes":"none",
        #     "amount_discount":"0.00",
        #     "amount_paid":"300.00",
        #     "cc_num": "XXXXXXXXXXXX4242",
        #  	  "cc_exp_date":"2021-08-01",
        #     "cc_cvv":"123",
        #     "billing_zip":"12345"}



# -- Queries end here -------------------------------------------------------------------------------

# Add Comment Here ie Shows All Meal Plan Info
class TemplateApi(Resource):
    def get(self):
        response = {}
        items = {}
        try:
            conn = connect()

            items = execute(""" SELECT
                                *
                                FROM
                                ptyd_meal_plans;""", 'get', conn)

            response['message'] = 'successful'
            response['result'] = items

            return response, 200
        except:
            raise BadRequest('Request failed, please try again later.')
        finally:
            disconnect(conn)

# -- START NOTIFICATIONS INFO -------------------------------------------------------------------------------
class Send_Notification(Resource):
    def post(self):
        hub = NotificationHub(NOTIFICATION_HUB_KEY, NOTIFICATION_HUB_NAME, isDebug)
        tags = request.form.get('tags')
        message = request.form.get('message')
        
        if tags is None:
            raise BadRequest('Request failed. Please provide the tag field.')
        if message is None:
            raise BadRequest('Request failed. Please provide the message field.')
        tags = tags.split(',')
        for tag in tags:
            alert_payload = {
                "aps" : { 
                    "alert" : message, 
                }, 
            }
            # hub.send_apple_notification(alert_payload, tags = "default")
            hub.send_apple_notification(alert_payload, tags = tag)
            fcm_payload = {
                "data":{"message": message}
            }
            # hub.send_gcm_notification(fcm_payload, tags = "default")
            hub.send_gcm_notification(fcm_payload, tags = tag)
        return 200

class Get_Registrations_From_Tag(Resource):
    def get(self, tag):
        hub = NotificationHub(NOTIFICATION_HUB_KEY, NOTIFICATION_HUB_NAME, isDebug)
        if tag is None:
            raise BadRequest('Request failed. Please provide the tag field.')
        response = hub.get_all_registrations_with_a_tag(tag)
        response = str(response.read())
        print(response)
        return response,200

class Create_or_Update_Registration_iOS(Resource):
    def post(self):
        hub = NotificationHub(NOTIFICATION_HUB_KEY, NOTIFICATION_HUB_NAME, isDebug)
        registration_id = request.form.get('registration_id')
        device_token = request.form.get('device_token')
        tags = request.form.get('tags')
        
        if tags is None:
            raise BadRequest('Request failed. Please provide the tags field.')
        if registration_id is None:
            raise BadRequest('Request failed. Please provide the registration_id field.')
        if device_token is None:
            raise BadRequest('Request failed. Please provide the device_token field.')

        response = hub.create_or_update_registration_iOS(registration_id, device_token, tags)

        return response.status

class Update_Registration_With_GUID_iOS(Resource):
    def post(self):
        hub = NotificationHub(NOTIFICATION_HUB_KEY, NOTIFICATION_HUB_NAME, isDebug)
        guid = request.form.get('guid')
        tags = request.form.get('tags')
        if guid is None:
            raise BadRequest('Request failed. Please provide the guid field.')
        if tags is None:
            raise BadRequest('Request failed. Please provide the tags field.')
        response = hub.get_all_registrations_with_a_tag(guid)
        xml_response = str(response.read())[2:-1]
        # root = ET.fromstring(xml_response)
        xml_response_soup = BeautifulSoup(xml_response,features="html.parser")
        appleregistrationdescription = xml_response_soup.feed.entry.content.appleregistrationdescription
        registration_id = appleregistrationdescription.registrationid.get_text()
        device_token = appleregistrationdescription.devicetoken.get_text()
        old_tags = appleregistrationdescription.tags.get_text().split(",")
        tags = tags.split(",")
        new_tags = set(old_tags + tags)
        new_tags = ','.join(new_tags)
        print(f"tags: {old_tags}\ndevice_token: {device_token}\nregistration_id: {registration_id}")
        
        if device_token is None or registration_id is None:
            raise BadRequest('Something went wrong in retriving device_token and registration_id')
        
        response = hub.create_or_update_registration_iOS(registration_id, device_token, new_tags)
        # for type_tag in root.findall('feed/entry/content/AppleRegistrationDescription'):
        #     value = type_tag.get('Tags')
        #     print(value)
        # print("\n\n--- RESPONSE ---")
        # print(str(response.status) + " " + response.reason)
        # print(response.msg)
        # print(response.read())
        # print("--- END RESPONSE ---")
        return response.status

class Update_Registration_With_GUID_Android(Resource):
    def post(self):
        hub = NotificationHub(NOTIFICATION_HUB_KEY, NOTIFICATION_HUB_NAME, isDebug)
        guid = request.form.get('guid')
        tags = request.form.get('tags')
        if guid is None:
            raise BadRequest('Request failed. Please provide the guid field.')
        if tags is None:
            raise BadRequest('Request failed. Please provide the tags field.')
        response = hub.get_all_registrations_with_a_tag(guid)
        xml_response = str(response.read())[2:-1]
        # root = ET.fromstring(xml_response)
        xml_response_soup = BeautifulSoup(xml_response,features="html.parser")
        gcmregistrationdescription = xml_response_soup.feed.entry.content.gcmregistrationdescription
        registration_id = gcmregistrationdescription.registrationid.get_text()
        gcm_registration_id = gcmregistrationdescription.gcmregistrationid.get_text()
        old_tags = gcmregistrationdescription.tags.get_text().split(",")
        tags = tags.split(",")
        new_tags = set(old_tags + tags)
        new_tags = ','.join(new_tags)
        print(f"tags: {old_tags}\nregistration_id: {registration_id}\ngcm_registration_id: {gcm_registration_id}")
        
        if gcm_registration_id is None or registration_id is None:
            raise BadRequest('Something went wrong in retriving gcm_registration_id and registration_id')
        
        response = hub.create_or_update_registration_android(registration_id, gcm_registration_id, new_tags)
        return response.status

# -- END NOTIFICATIONS INFO -------------------------------------------------------------------------------




# Define API routes

# Books
api.add_resource(AllBooks, '/api/v2/AllBooks')
api.add_resource(AllUsers, '/api/v2/AllUsers')
api.add_resource(AllAuthors, '/api/v2/AllAuthors')
api.add_resource(AllReaders, '/api/v2/AllReaders')
api.add_resource(BooksByAuthorEmail, '/api/v2/BooksByAuthorEmail/<string:user_email>')
api.add_resource(BooksByAuthorUID, '/api/v2/BooksByAuthorUID/<string:author_uid>')

# Other
api.add_resource(Businesses, '/api/v2/businesses')
api.add_resource(SubscriptionsbyBusiness, '/api/v2/subscriptionsByBusiness/<string:business_uid>')
api.add_resource(CouponDetails, '/api/v2/couponDetails/<string:coupon_id>', '/api/v2/couponDetails')
api.add_resource(RefundDetails, '/api/v2/refundDetails')
api.add_resource(RefundDetailsNEW, '/api/v2/refundDetailsNEW')
api.add_resource(PurchaseData, '/api/v2/purchaseData')
api.add_resource(MSPurchaseData, '/api/v2/MSpurchaseData')


# Run on below IP address and port
# Make sure port number is unused (i.e. don't use numbers 0-1023)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4000)

