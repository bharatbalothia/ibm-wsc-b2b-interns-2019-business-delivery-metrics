import re
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_file
from flask_session import Session, FileSystemSessionInterface
import couchdb
import datetime
from ldap3 import *
from functools import wraps
from analysis import SentimentSentiwordnet, SentimentWatsonNLU
from utility import correctString, try_parsing_date

app = Flask(__name__)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)


user = "admin"
password = "admin"
couch = couchdb.Server("http://%s:%s@9.199.145.49:5984/" % (user, password))
db = couch['salesforce_improved']



def sentimentAnalyser(body):
    contents = []
    for data in body:
        analyse_this = correctString(data['body'])
        #resp = SentimentSentiwordnet.sentiwordNLU(analyse_this)
        resp = SentimentSentiwordnet.sentiwordNLU(analyse_this)
        content = data
        content['score'] = resp[0]
        content['label'] = resp[1]
        content['body'] = analyse_this
        contents.append(content)
        #print(contents)
        #print(i['score'] + "     " + i['label'] + "         " + analyse_this)
    if session['message_content'] is None:
        session['message_content'] = contents
    else:
        session['message_content'] += contents
    #print(session['message_content'])
    return contents


@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in'] == True:
        return render_template('Dashboard.html')
    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        POST_USERNAME = str(request.form['username'])
        POST_PASSWORD = str(request.form['password'])
        db2 = couch['loginuser']
        for i in db2:
            if db2[i]['type'] == 'user':
                if db2[i]['username'] == POST_USERNAME:
                    session['logged_in'] = True
                    session['username'] = POST_USERNAME

                    # flash('You are now logged in', 'success')
                    return redirect(url_for('index'))


        server = Server('ldap://bluepages.ibm.com', get_info=ALL)
        c = Connection(server, user="", password="", raise_exceptions=False)
        noUseBool = c.bind()

        checkUserIBM = c.search(search_base='ou=bluepages,o=ibm.com',
                                search_filter='(mail=%s)' % (POST_USERNAME),
                                search_scope=SUBTREE,
                                attributes=['dn', 'givenName'])

        if (checkUserIBM == False):
            session['authorized'] = 0
            error = 'Invalid login'
            return render_template('login.html', error=error)

        # get the username of the emailID and authenticate password
        userName = c.entries[0].givenName[0]
        uniqueID = c.response[0]['dn']
        c2 = Connection(server, uniqueID, POST_PASSWORD)
        isPassword = c2.bind()

        if (isPassword == False):
            session['authorized'] = 0
            error = 'Invalid login'
            return render_template('login.html', error=error)

        # now search group
        checkIfAdminGroup = c.search(search_base='cn=RSC_B2B,ou=memberlist,ou=ibmgroups,o=ibm.com',
                                     search_filter='(uniquemember=%s)' % (str(uniqueID)),
                                     search_scope=SUBTREE,
                                     attributes=['dn'])

        if (checkIfAdminGroup == False):
            session['authorized'] = 0
            error = 'Invalid login'
            return render_template('login.html', error=error)

        # control reaches here if user password and group authentication is successful

        session['logged_in'] = True
        session['username'] = userName

        #flash('You are now logged in', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap

@app.route('/talk', methods=['GET', 'POST'])
@is_logged_in
def talk():
    session['message_content'] = None
    case_numbers = request.form['search']
    from_date = request.form['fromDate']
    to_date = request.form['toDate']

    cases = case_numbers.split(",")
    resp = []
    for case in cases:
        if case in db:
            body = db[case]['Body']
            data_to_be_analysed = []
            for id in body:
                body[id]['case_number'] = case
                try:
                    creation_date = body[id]['creation_date'].split()[0]
                    print(creation_date)
                    creation_date = try_parsing_date(creation_date).strftime('%Y-%m-%d')
                    if from_date <= creation_date <= to_date :
                        data_to_be_analysed.append(body[id])
                except:
                    pass
            analysed_case = sentimentAnalyser(data_to_be_analysed)
            resp = resp + analysed_case
    return render_template('Dashboard.html', data=resp)


@app.route('/message_review/<string:message_id>', methods=['POST'])
@is_logged_in
def message_review(message_id):
    db3 = couch['salesforce_response']
    contents = session.get('message_content')
    response = request.form['response']
    remark = request.form['remarks']
    doc = {}
    doc['reviewed'] = {}
    for data in contents:
        #print(data)
        case_id = data['case_number']
        if data['_id'] == message_id and case_id not in db3:
            doc['_id'] = case_id
            doc['reviewed'][message_id] = data
            doc['reviewed'][message_id]['response'] = response
            doc['reviewed'][message_id]['reviewed_by'] = session['username']
            doc['reviewed'][message_id]['remarks'] = remark
            db3.save(doc)
            #print(doc)
            break
        elif data['_id'] == message_id and case_id in db3 :
            document = db3[case_id]
            document['reviewed'][message_id] = data
            document['reviewed'][message_id]['response'] = response
            document['reviewed'][message_id]['reviewed_by'] = session['username']
            document['reviewed'][message_id]['remarks'] = remark
            db3.save(document)
            break

    contents = [d for d in contents if d.get('_id') != message_id]
    session['message_content'] = contents
    #flash('Event Deleted', 'success')
    return render_template('Dashboard.html', data=contents)


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    session['logged_in'] = False
    flash('You have logged out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = 'secret12345'
    app.run(host='127.0.0.1',port=5000,debug=True)
