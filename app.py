import re
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_file
from flask_session import Session, FileSystemSessionInterface
import couchdb
import datetime
from ldap3 import *
from authenticate import *
from functools import wraps
from analysis import SentimentSentiwordnet, SentimentWatsonNLU, Escalation_classifier
from utility import correctString, try_parsing_date

app = Flask(__name__)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=20)


user = "admin"
password = "admin"
couch = couchdb.Server("http://%s:%s@9.199.145.49:5984/" % (user, password))
db = couch['salesforce_improved']
db2 = couch['salesforce_type']



def sentimentAnalyser(body):
    contents = []
    for data in body:
        analyse_this = correctString(data['body'])
        resp = SentimentSentiwordnet.sentiwordNLU(analyse_this)
        #resp = SentimentWatsonNLU.watsonNLU(analyse_this)
        #nlc_class = Escalation_classifier.watsonClassifer(analyse_this)
        content = data
        if float(resp[0]) == 0.0:
            pass
        else:
            content['score'] = float(resp[0])
            #content['class'] = nlc_class
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
        return render_template('home.html')
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

        isLoged = authenticate(POST_USERNAME,POST_PASSWORD)
        if not isLoged[0] :
            session['authorized'] = 0
            error = 'Invalid login'
            return render_template('login.html', error=error)
        else:
            session['logged_in'] = True
            session['username'] = isLoged[1]

            # flash('You are now logged in', 'success')
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


@app.route('/dashboard', methods=['GET', 'POST'])
@is_logged_in
def dashboard():
    return render_template('Dashboard.html')


@app.route('/delivery_dashboard', methods=['GET', 'POST'])
@is_logged_in
def delivery_dashboard():
    return render_template('deliveryDashboard.html')


@app.route('/per_dashboard')
@is_logged_in
def per_dashboard():
    return render_template('under_construction.html')


@app.route('/mapping_dashboard')
@is_logged_in
def mapping_dashboard():
    return render_template('under_construction.html')


@app.route('/account_dashboard')
@is_logged_in
def account_dashboard():
    return render_template('under_construction.html')


@app.route('/timespent_dashboard')
@is_logged_in
def timespent_dashboard():
    return render_template('under_construction.html')


@app.route('/caseprofile/<string:case_id>')
def caseprofile(case_id):
    id = case_id
    graphData = [['Creation Date', 'NLU Score']]
    other_info = []
    body = db[id]['Body']
    for i in body:
        if body[i]['creation_date'] != "":
            creation_date = try_parsing_date(body[i]['creation_date'].split()[0]).strftime('%Y-%m-%d')
            if 'NLUscore' in body[i]:
                NLUscore = float(body[i]['NLUscore'])
            else:
                response = SentimentSentiwordnet.sentiwordNLU(body[i]['body'])
                NLUscore = float(response[0])
                body[i]['NLUscore'] = NLUscore
                body[i]['NLUsentiment'] = response[1]
            graphData.append([creation_date, NLUscore])
            other_info.append(body[i])
    return render_template('caseProfile.html',graphData=graphData,data = other_info)


@app.route('/talk', methods=['GET', 'POST'])
@is_logged_in
def talk():
    session['message_content'] = None
    case_numbers = request.form['search']
    from_date = request.form['fromDate']
    to_date = request.form['toDate']

    if len(case_numbers)>3:
        cases = case_numbers.split(",")
        resp = []
        for case in cases:
            if case in db:
                body = db[case]['Body']
                if case in db2:
                    severity = db2[case]['Severity Level'].split()[0]
                else:
                    severity = "0"
                data_to_be_analysed = []
                for id in body:
                    body[id]['case_number'] = case
                    body[id]['severity'] = severity
                    try:
                        creation_date = body[id]['creation_date'].split()[0]
                        print(creation_date)
                        creation_date = try_parsing_date(creation_date).strftime('%Y-%m-%d')
                        if body[id]['person_type'] == 'Customer' and from_date <= creation_date <= to_date :
                            data_to_be_analysed.append(body[id])
                    except:
                        pass
                analysed_case = sentimentAnalyser(data_to_be_analysed)
                resp = resp + analysed_case
        resp = sorted(resp, key=lambda i: i['severity'], reverse=True)
        return render_template('Dashboard.html', data=resp)
    else:
        resp = []
        print(from_date,to_date)
        for row2 in db.view('_design/date-range/_view/date-range', startkey=from_date, endkey=to_date):
            case = row2.id
            print(case)
            if case in db2:
                severity = db2[case]['Severity Level'].split()[0]
            else:
                severity = "0"
            body = row2.value
            data_to_be_analysed = []
            for id in body:
                body[id]['case_number'] = case
                body[id]['severity'] = severity
                try:
                    creation_date = body[id]['creation_date'].split()[0]
                    creation_date = try_parsing_date(creation_date).strftime('%Y-%m-%d')
                    if body[id]['person_type'] == 'Customer' and from_date <= creation_date <= to_date:
                        print(creation_date)
                        data_to_be_analysed.append(body[id])
                except:
                    pass
            print(len(data_to_be_analysed))
            if len(data_to_be_analysed) > 0:
                analysed_case = sentimentAnalyser(data_to_be_analysed)
                resp = resp + analysed_case
        resp = sorted(resp, key=lambda i: i['severity'], reverse=True)
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
    contents = sorted(contents, key=lambda i: i['severity'], reverse=True)
    return render_template('Dashboard.html', data=contents)


@app.errorhandler(500)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('500.html'), 500

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('500.html'), 500

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
