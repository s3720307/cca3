import boto3
import botocore.exceptions
import hmac
import hashlib
import base64
import json
import datetime
import requests
from io import BytesIO

from flask import Flask, render_template, request, redirect, session, url_for, flash
application = Flask(__name__)
application.secret_key = "random"

##PK
#USER_POOL_ID = 'us-east-2_ruiTY0hP5'
#CLIENT_ID = '14d1pjd3tjchpg77kcld5oam6q'
#CLIENT_SECRET = 'jgrtpnhoq01h77tt9kjh74k1gn22r6l4l7g3ctc8bhtfoigrmkq'
#client = boto3.client('cognito-idp', region_name='us-east-2')
#dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
#s3client = boto3.client('s3', region_name='us-east-2')
#tasktable = dynamodb.Table('Task')
#subtable = dynamodb.Table('Subtask')
#bucketname = 'cca3images'
#bucketnameuser = 'cca3userprofiles'

#Sohee
USER_POOL_ID = 'us-east-1_ML8n8zEda'
CLIENT_ID = '7e6fl49b57k982roaudequp1hi'
CLIENT_SECRET = '6373u966d5p8g89e2hil3b5qpg22nq2t50jkjr1n9m03c35kd0f'

client = boto3.client('cognito-idp', region_name='us-east-1')

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tasktable = dynamodb.Table('Task')
subtable = dynamodb.Table('Subtask')

s3client = boto3.client('s3', region_name='us-east-1')
bucketname = 'cca3imgs'
bucketnameuser = 'cca3users'



def get_secret_hash(username):
    msg = username + CLIENT_ID
    dig = hmac.new(str(CLIENT_SECRET).encode('utf-8'), 
        msg = str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    d2 = base64.b64encode(dig).decode()
    return d2

# add user to the user pool
# return '' or exception message
# def cognito_sign_up(email, username, password, name):
#     try:
#         response = client.sign_up(
#             ClientId=CLIENT_ID,
#             SecretHash=get_secret_hash(username),
#             Username=username,
#             Password=password, 
#             UserAttributes=[
#                 {
#                     'Name': "name",
#                     'Value': name
#                 },
#                 {
#                     'Name': "email",
#                     'Value': email
#                 }
#             ],
#             ValidationData=[
#                 {
#                     'Name': "email",
#                     'Value': email
#                 },
#                 {
#                     'Name': "custom:username",
#                     'Value': username
#                 }
#             ]
#         )
#     except Exception as e:
#         return e

#     return ''

# add user to the user pool
# return '' or exception message
def cognito_sign_up_new(email, username, password, firstname, lastname, phone, img):
    try:
        response = client.sign_up(
            ClientId=CLIENT_ID,
            SecretHash=get_secret_hash(username),
            Username=username,
            Password=password, 
            UserAttributes=[
                {
                    'Name': "given_name",
                    'Value': firstname
                },
                {
                    'Name': "family_name",
                    'Value': lastname
                },
                {
                    'Name': "phone_number",
                    'Value': phone
                },
                {
                    'Name': "picture",
                    'Value': img
                },
                {
                    'Name': "email",
                    'Value': email
                }
            ],
            ValidationData=[
                {
                    'Name': "email",
                    'Value': email
                },
                {
                    'Name': "custom:username",
                    'Value': username
                }
            ]
        )
    except Exception as e:
        return e

    return ''

# check if user can provide a correct code sent
# return '' or exception message
def cognito_confirm_sign_up(username, code):
    try:
        response = client.confirm_sign_up(
            ClientId = CLIENT_ID,
            SecretHash = get_secret_hash(username),
            Username = username,
            ConfirmationCode = code,
            ForceAliasCreation = False,
        )
    except Exception as e:
        return e
    
    return ''

# get user info with username and password
# currently using this only to get access token
# return response or {}
def initiate_auth(username, password):
    try:
        response = client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'SECRET_HASH': get_secret_hash(username),
                'PASSWORD': password,
            },
            ClientMetadata={
                'username': username,
                'password': password,
            }
        )
    except Exception as e:
        print(e)
        return {}, e

    # response will look like:
    # {
    #     'ChallengeParameters': {},
    #     'AuthenticationResult':{
    #         'AccessToken': 'eyJraWQiOiJ5aXdpZHBsR2Z1S29PY3B2ckRXZXpsZmM0S longer than this',
    #         'ExpiresIn': 3600,
    #         'TokenType': 'Bearer',
    #         'RefreshToken': 'eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxn longer than this',
    #         'IdToken': 'eyJraWQiOiJJcThtb2Rrc09LdHVkSkJtMmtvR3hKblZnSHRiS longer than this'
    #     },
    #     'ResponseMetadata': {
    #         'RequestId': 'ab364442-3ec0-4163-9615-ff93b0deddcc',
    #         'HTTPStatusCode': 200,
    #         'HTTPHeaders': {
    #             'date': 'Wed, 02 Jun 2021 10:42:16 GMT',
    #             'content-type': 'application/x-amz-json-1.1',
    #             'content-length': '3791',
    #             'connection': 'keep-alive',
    #             'x-amzn-requestid': 'ab364442-3ec0-4163-9615-ff93b0deddcc'
    #         },
    #         'RetryAttempts': 0
    #     }
    # }
    return response, ''

# get user info with access token
# return response
def cognito_get_user(accesstoken):
    try:
        response = client.get_user(
            AccessToken = accesstoken
        )
    except Exception as e:
        print(e)
    
    # new user attributes:
    # loggedinEmail, loggedinFname, loggedinLname, loggedinPhone, loggedinPic, loggedinUsername
    # response will look like:
    # {
    #     'Username': 'user444',
    #     'UserAttributes':
    #         [
    #             {'Name': 'sub', 'Value': 'd0913529-85ef-4525-bc4f-5bb027de3a20'},
    #             {'Name': 'email_verified', 'Value': 'true'},
    #             {'Name': 'name', 'Value': 'name TEST 4'},
    #             {'Name': 'email', 'Value': 'icotpcatudnojrvuhw@niwghx.com'}
    #         ],
    #         'ResponseMetadata': {
    #             'RequestId': '6125862e-7c1f-46be-9e1a-f586bdaac8a2',
    #             'HTTPStatusCode': 200,
    #             'HTTPHeaders': {
    #                 'date': 'Wed, 02 Jun 2021 11:09:26 GMT',
    #                 'content-type': 'application/x-amz-json-1.1',
    #                 'content-length': '239',
    #                 'connection': 'keep-alive',
    #                 'x-amzn-requestid': '6125862e-7c1f-46be-9e1a-f586bdaac8a2'
    #             },
    #             'RetryAttempts': 0
    #         }
    # }
    return response

def emptySession():
    for key in list(session.keys()):
        session.pop(key, None)

def isLoggedIn():
    for key in list(session.keys()):
        if key != '_flashes':
            return True
    return False
    # return session != {}

def updateUser(fname='', lname='', phone='', img='', removeimg=False):
    attributes = []

    if fname != '':
        attributes.append({ 'Name': "given_name", 'Value': fname })
        print('changing fname now')
    if lname != '':
        attributes.append({ 'Name': "family_name", 'Value': lname })
        print('changing lname now')
    if phone != '':
        attributes.append({ 'Name': "phone_number", 'Value': phone })
        print('changing phone now')
    if img != '':
        attributes.append({ 'Name': "picture", 'Value': img })
        print('changing img now')
    if removeimg:
        attributes.append({ 'Name': "picture", 'Value': '' })
        print('removing img now')

    try:
        response = client.update_user_attributes(
            UserAttributes=attributes,
            # [
                # {
                #     'Name': "given_name",
                #     'Value': fname
                # },
                # {
                #     'Name': "family_name",
                #     'Value': lname
                # },
                # # {
                # #     'Name': "phone_number",
                # #     'Value': phone
                # # },
                # # {
                # #     'Name': "picture",
                # #     'Value': img
                # # },
            # ],
            AccessToken=session['loggedinAccesstoken']
        )
    except Exception as e:
        print(e)
        return e

    return ''

# return current timestamp string
def getTimestamp():
    return str(datetime.datetime.now())

# return datetime object
def strToTime(timestring):
    return datetime.datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S.%f')

# # Owner, TaskID, Title, Desc, Done, Fav
# # returns None if task doesn't exist
# def getTask(taskid, username):
#     response = tasktable.get_item(Key = { 'TaskID': taskid, 'Owner': username })
#     return response.get('Item')

# # ParentTask, SubtaskID, Title, Desc, Due, Done, Image, Url
# # returns None if subtask doesn't exist
# def getSubtask(subtaskid, parenttask):
#     response = subtable.get_item(Key = { 'SubtaskID': subtaskid, 'ParentTask': parenttask })
#     return response.get('Item')

def addTask(title, desc, done, fav):
    response = tasktable.put_item(
        Item = {
            'Owner': session['loggedinUsername'],
            'TaskID': getTimestamp(),
            'Email': session['loggedinEmail'],
            'Title': title,
            'Desc': desc,
            'Done': done,
            'Fav': fav
        }
    )

def addSubtask(parenttask, subtaskid, title, desc, due, done, image, url):
    response = subtable.put_item(
        Item = {
            'ParentTask': parenttask,
            'SubtaskID': subtaskid,
            'Title': title,
            'Desc': desc,
            'Due': due,
            'Done': done,
            'Image': image,
            'Url': url
        }
    )

def getTaskIDtoSort(alltasks):
    return alltasks['TaskID']

# returns [] if empty
def getAllTasksByCurrentUser():
    scan_kwargs = {
        'FilterExpression': "#o = :u",
        "ExpressionAttributeValues": {
            ':u': session['loggedinUsername']
        },
        'ExpressionAttributeNames': {
            "#o": "Owner"
        }
    }
    response = tasktable.scan(**scan_kwargs)

    alltasks = response.get("Items")
    alltasks.sort(key=getTaskIDtoSort)
    return alltasks

def getSubtaskIDtoSort(allsubtasks):
    return allsubtasks['SubtaskID']

# returns [] if empty
def getAllFavouritedTasksByCurrentUser():
    scan_kwargs = {
        'FilterExpression': "#o = :u and Fav=:f",
        "ExpressionAttributeValues": {
            ':u': session['loggedinUsername'],
            ':f': True
        },
        'ExpressionAttributeNames': {
            "#o": "Owner"
        }
    }
    response = tasktable.scan(**scan_kwargs)

    alltasks = response.get("Items")
    alltasks.sort(key=getTaskIDtoSort)
    return alltasks

# returns [] if empty
def getAllSubtasksByParent(parenttask):
    scan_kwargs = {
        'FilterExpression': "ParentTask = :p",
        "ExpressionAttributeValues": {
            ':p': parenttask
        }
    }
    response = subtable.scan(**scan_kwargs)

    allsubtasks = response.get("Items")
    allsubtasks.sort(key=getSubtaskIDtoSort)
    return allsubtasks

def updateTask(taskid, title, desc, done, fav):
    tasktable.update_item(
        Key = { 'TaskID': taskid, 'Owner': session['loggedinUsername'] },
        UpdateExpression = "set Title=:t, #d=:de, Done=:do, Fav=:f",
        ExpressionAttributeValues = {
            ':t': title,
            ':de': desc,
            ':do': done,
            ':f': fav
        },
        ExpressionAttributeNames = {
            "#d": "Desc"
        }
    )

def updateTaskDone(taskid, done):
    tasktable.update_item(
        Key = { 'TaskID': taskid, 'Owner': session['loggedinUsername'] },
        UpdateExpression = "set Done=:do",
        ExpressionAttributeValues = {
            ':do': done
        }
    )

def updateSubtask(parenttask, subtaskid, title, desc, due, done, image, url):
    subtable.update_item(
        Key = { 'ParentTask': parenttask, 'SubtaskID': subtaskid },
        UpdateExpression = "set Title=:t, #d=:de, Due=:du, Done=:do, Image=:i, #u=:u",
        ExpressionAttributeValues = {
            ':t': title,
            ':de': desc,
            ':du': due,
            ':do': done,
            ':i': image,
            ':u': url
        },
        ExpressionAttributeNames = {
            "#d": "Desc",
            "#u": "Url"
        }
    )

# to check form checkboxes
def isChecked(checked):
    if checked:
        return 'checked'
    return ''

def isKeyIncluded(key, dictionary):
    for k in list(dictionary.keys()):
        if k == key:
            return True
    return False

def deleteTask(taskid):
    tasktable.delete_item(Key = { 'TaskID': taskid, 'Owner': session['loggedinUsername'] })

def deleteSubtask(parenttask, subtaskid, image):
    subtable.delete_item(Key = { 'ParentTask': parenttask, 'SubtaskID': subtaskid })

    if image != '':
        deleteFromS3(image, 'task')

def hasSubtask(parenttask):
    if getAllSubtasksByParent(parenttask) == []:
        return False
    return True

# returns formatted date 'yyyy-mm-dd' to 'dd Mon yyyy'
# or '' to ''
def formatDate(original):
    if original == '':
        return ''
    month = original[5:7]
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return original[8:] + ' ' + months[int(month)-1] + ' ' + original[:4]

def getExtension(filename):
    extension = filename[filename.rfind('.'):len(filename)]
    return extension

# returns new file name including extension
def uploadToS3(file, subtaskid):
    extension = getExtension(file.filename)
    realfilename = subtaskid + extension

    response = s3client.upload_fileobj(file, bucketname, realfilename, ExtraArgs={'ACL': 'public-read'})
    return realfilename

def deleteFromS3(filename, table):
    if table == 'task':
        thisbucketname = bucketname
    if table == 'user':
        thisbucketname = bucketnameuser
    
    response = s3client.delete_object(Bucket = thisbucketname, Key = filename)

def getUserDetails(accesstoken):
    try:
        getuser = cognito_get_user(accesstoken)

        emptySession()

        # does not throw an error even if a desired attribute does not exist
        session['loggedinAccesstoken'] = accesstoken
        session['loggedinUsername'] = getuser['Username']
        for a in getuser['UserAttributes']:
            if a['Name'] == 'email':
                session['loggedinEmail'] = a['Value']
            if a['Name'] == 'given_name':
                session['loggedinFname'] = a['Value']
            if a['Name'] == 'family_name':
                session['loggedinLname'] = a['Value']
            if a['Name'] == 'phone_number':
                session['loggedinPhone'] = a['Value']
            if a['Name'] == 'picture':
                session['loggedinPic'] = a['Value']
    except Exception as e:
        print(e)
        return e

    return ''

def uploadProfileImgToS3(file, imgname):
    response = s3client.upload_fileobj(file, bucketnameuser, imgname, ExtraArgs={'ACL': 'public-read'})


@application.route("/")
def root():
    if isLoggedIn():
        return redirect("/home")
    else:
        return redirect('/login')
    return render_template("index.html")

@application.route("/register", methods=["GET", "POST"])
def register():
    if isLoggedIn():
        return redirect("/home")
    else:
        if request.method == "POST":
            email = request.form["register-em"]
            username = request.form["register-un"]
            password = request.form["register-pw"]
            firstname = request.form["register-fn"]
            lastname = request.form["register-ln"]
            phone = '+' + request.form["register-pn"].replace("+", "")
            img = request.files["register-pi"]
            realimgname = username + getExtension(img.filename)
            tryregistering = cognito_sign_up_new(email, username, password, firstname, lastname, phone, realimgname)

            if tryregistering == '': # no exception
                flash("Registration Successful..!!", 'success')
                uploadProfileImgToS3(img, realimgname)
                return redirect(url_for('verification', username=username))

            else: # somethings wrong
                flash(str(tryregistering), 'danger')
                return render_template("register.html")

            return redirect("/login")

        return render_template("register.html")

@application.route("/verification/<username>", methods=["GET", "POST"])
def verification(username):
    if request.method == "POST":
        code = request.form["verification-code"]
        tryverifying = cognito_confirm_sign_up(username, code)

        if tryverifying == '': # verified successfully
            flash("User verification successful..Please Login..!!", 'success')
            return redirect('/login')

        else: # not verified
            print(tryverifying)
            flash(str(tryverifying), 'danger')
            return render_template("verification.html", username=username)
    
    return render_template("verification.html", username=username)

@application.route("/login", methods=["GET", "POST"])
def login():
    if isLoggedIn():
        return redirect("/home")
    else:
        if request.method == "POST":
            username = request.form['login-un']
            password = request.form['login-pw']
            tryfindinguser = initiate_auth(username, password)
            
            if tryfindinguser[0] == {}: # not found
                flash("Login Failed..please try again", 'danger')
                return render_template("login.html")
            else: # user found
                accesstoken = tryfindinguser[0]['AuthenticationResult']['AccessToken']
                getUserDetails(accesstoken)
                flash("Login Successful..!!")
                return redirect('/home')

        return render_template("login.html")

@application.route("/logout", methods=["GET", "POST"])
def logout():
    emptySession()
    return redirect("/login")

@application.route("/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":

        # add task
        if request.form['tasks-type'] == 'add-task':
            addtaskdone = False
            addtaskfav = False
            if isKeyIncluded('add-task-done', request.form):
                addtaskdone = True
            if isKeyIncluded('add-task-fav', request.form):
                addtaskfav = True
            addTask(request.form['add-task-title'], request.form['add-task-desc'], addtaskdone, addtaskfav)

        # add subtask
        if request.form['tasks-type'] == 'add-subtask':
            currenttimestamp = getTimestamp()
            addsubdone = False
            imgname = ''
            if isKeyIncluded('add-sub-done', request.form):
                addsubdone = True
            if request.files['add-sub-image'].filename != '':
                imgname = uploadToS3(request.files['add-sub-image'], currenttimestamp)
            addSubtask(request.form['add-sub-parent'], currenttimestamp, request.form['add-sub-title'], request.form['add-sub-desc'], request.form['add-sub-due'], addsubdone, imgname, request.form['add-sub-url'])

        # update task
        if request.form['tasks-type'] == 'update-task':
            updatetaskdone = False
            taskfav = False
            if isKeyIncluded('update-task-done', request.form):
                updatetaskdone = True
            if isKeyIncluded('update-task-fav', request.form):
                taskfav = True
            updateTask(request.form['update-task-id'], request.form['update-task-title'], request.form['update-task-desc'], updatetaskdone, taskfav)

        # update subtask
        if request.form['tasks-type'] == 'update-subtask':
            updatesubdone = False
            imgname = ''
            if isKeyIncluded('update-sub-done', request.form):
                updatesubdone = True
            # if new image is uploaded
            if request.files['update-sub-image'].filename != '':
                # if old image exists
                if request.form['update-sub-image-old'] != '':
                    deleteFromS3(request.form['update-sub-image-old'], 'task')
                imgname = uploadToS3(request.files['update-sub-image'], request.form['update-sub-id'])
            # if new image is not uploaded
            else:
                # keep original image if exists
                if isKeyIncluded('update-sub-image-keep', request.form):
                    imgname = request.form['update-sub-image-old']
                # remove old image if exists
                else:
                    if request.form['update-sub-image-old'] != '':
                        deleteFromS3(request.form['update-sub-image-old'], 'task')
            updateSubtask(request.form['update-sub-parent'], request.form['update-sub-id'], request.form['update-sub-title'], request.form['update-sub-desc'], request.form['update-sub-due'], updatesubdone, imgname, request.form['update-sub-url'])

        # delete task
        if request.form['tasks-type'] == 'delete-task':
            deleteTask(request.form['delete-task-id'])
            for st in getAllSubtasksByParent(request.form['delete-task-id']):
                deleteSubtask(request.form['delete-task-id'], st['SubtaskID'], st['Image'])

        # delete subtask
        if request.form['tasks-type'] == 'delete-subtask':
            deleteSubtask(request.form['delete-sub-parent'], request.form['delete-sub-id'], request.form['delete-sub-image'])

        # check task done state
        for t in getAllTasksByCurrentUser():
            # print('Task:', t)
            subtaskexist = False
            subtaskdonestate = True
            for s in getAllSubtasksByParent(t['TaskID']):
                # print('Subtask:', s)
                subtaskexist = True
                if s['Done'] == False:
                    subtaskdonestate = False
            # print(subtaskdonestate)
            if subtaskexist:
                if subtaskdonestate != t['Done']:
                    # print('no match')
                    updateTaskDone(t['TaskID'], subtaskdonestate)

    return render_template("tasks.html",
        tasks=getAllTasksByCurrentUser(),
        getAllSubtasksByParent=getAllSubtasksByParent,
        isChecked=isChecked,
        formatDate=formatDate,
        hasSubtask=hasSubtask,
        bucketname=bucketname)

@application.route("/home", methods=["GET", "POST"])
def home():
    # print(session)
    # if request.method == "POST":
    #     return
    name = ''
    try:
        name = session['loggedinFname']
    except:
        name = session['loggedinUsername']
    
    favourited = getAllFavouritedTasksByCurrentUser()
    
    return render_template("home.html", favourited=favourited, name=name)
        # tasks=getAllTasksByCurrentUser(),
        # getAllSubtasksByParent=getAllSubtasksByParent,
        # isChecked=isChecked,
        # formatDate=formatDate)

@application.route("/user", methods=["GET", "POST"])
def user():
    # email = fname = lname = phone = pic = ''
    # try:
    #     email = session['loggedinEmail']
    # except:
    #     pass
    # try:
    #     fname = session['loggedinFname']
    # except:
    #     pass
    # try:
    #     lname = session['loggedinLname']
    # except:
    #     pass
    # try:
    #     phone = session['loggedinPhone']
    # except:
    #     pass
    # try:
    #     pic = session['loggedinPic']
    # except:
    #     pass

    if request.method == "POST":
        if request.form['profile-change-type'] == 'change-img':
            print('change img')
            print(request.files)
            newimg = request.files['update-user-image']

            # delete old image
            if isKeyIncluded('update-user-image-delete', request.form):
                print('delete current picture')
                ## update dynamodb img to ''
                updateUser(removeimg=True)
                ## remove image from s3
                deleteFromS3(request.form['update-user-image-old'], 'user')
            
            # new image is added
            if newimg.filename != '':
                # old image exists
                if request.form['update-user-image-old']:
                    print('replace image')
                    ## remove old image from s3
                    deleteFromS3(request.form['update-user-image-old'], 'user')

                ## add image to s3
                print('add new image')
                realimgname = session['loggedinUsername'] + getExtension(newimg.filename)
                uploadProfileImgToS3(newimg, realimgname)
                ## update dynamodb img to new
                updateUser(img=realimgname)

        if request.form['profile-change-type'] == 'change-name':
            newfname = request.form['update-user-fname']
            newlname = request.form['update-user-lname']
            updateUser(fname=newfname, lname=newlname)

        if request.form['profile-change-type'] == 'change-phone':
            # request.form['update-user-phone']
            print(type(request.form['update-user-phone']))
            newphone = '+' + request.form['update-user-phone'].replace("+", "")
            updateUser(phone=newphone)
        
            # tryfindinguser = initiate_auth(username, password)[0]['AuthenticationResult']['AccessToken']

        getUserDetails(session['loggedinAccesstoken'])
        print('user details updated')

    fname = lname = phone = pic = ''
    try:
        fname = session['loggedinFname']
    except:
        pass
    try:
        lname = session['loggedinLname']
    except:
        pass
    try:
        phone = session['loggedinPhone']
    except:
        pass
    try:
        pic = session['loggedinPic']
    except:
        pass

    return render_template("user.html", bucketname=bucketnameuser,
        username=session['loggedinUsername'], email=session['loggedinEmail'],
        fname=fname, lname=lname, phone=phone, pic=pic)

if __name__ == "__main__":
    application.run(debug=True)
