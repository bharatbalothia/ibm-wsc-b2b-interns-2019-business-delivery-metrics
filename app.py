import re
import json
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_file
from flask_session import Session, FileSystemSessionInterface
import couchdb
import csv
from werkzeug.utils import secure_filename
import datetime
from ldap3 import *
from authenticate import *
from functools import wraps
from analysis import SentimentSentiwordnet, SentimentWatsonNLU, Escalation_classifier
from utility import correctString, try_parsing_date
import resourse_recommend
import ibm_db
import uuid
import Db2DataAcess as dao
import SentimentScore

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
#couch = couchdb.Server("http://%s:%s@9.199.145.49:5984/" % (user, password))
#db = couch['salesforce_improved']
#db2 = couch['salesforce_type']

conn = ibm_db.connect("DATABASE=SFA;HOSTNAME=9.30.161.135;PORT=50001;PROTOCOL=TCPIP;UID=db2inst1;PWD=db@inst!;", "", "")


def sentimentAnalyser(body):
    contents = []
    for data in body:
        content = data
        analyse_this = correctString(data['body'])
        if 'NLUscore' in data:
            content['score'] = float(data['NLUscore'])
            # content['class'] = nlc_class
            content['label'] = data['NLUsentiment']
            content['body'] = analyse_this
            contents.append(content)
        else:
            resp = SentimentSentiwordnet.sentiwordNLU(analyse_this)
            #resp = SentimentWatsonNLU.watsonNLU(analyse_this)
            #nlc_class = Escalation_classifier.watsonClassifer(analyse_this)
            print('this case number does not have scores',data['case_number'])
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
        if "robin" == POST_USERNAME:
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
    data = resourse_recommend.account_list()
    return render_template('recommned.html',account_list = data)

@app.route('/recommender',methods=['GET', 'POST'])
@is_logged_in
def recommender():
    #account_name = str(request.form['account'])
    senders_list = request.files['delivery_file']
    senders_location = secure_filename(senders_list.filename)
    senders_list.save(senders_location)
    csvfile1 = open(senders_location, 'rt')
    reader1 = csv.DictReader(csvfile1)
    resp = {}
    resp = reader1

    with open(senders_location, 'r') as csvinput:
        with open('C:\\Users\\RajnishKumarVENDORRo\\PycharmProjects\\CaseClassification\\outputfiles\\'+senders_list.filename, 'w+') as csvoutput:
            writer = csv.writer(csvoutput, lineterminator='\n')
            reader = csv.reader(csvinput)

            all = []
            row = next(reader)
            row.append('Direction')
            row.append('Recommendation Date')
            row.append('Recommended Resource')
            all.append(row)
            for row in reader:
                data = resourse_recommend.recommend(row[3], row[6])
                row.append("inflow" if "Inflow" in senders_list.filename else "outflow")
                row.append(datetime.datetime.today().strftime('%Y-%m-%d'))
                row.append(data[0]['Resourse_id'] if len(data) > 0 else "No resource To recommend")
                all.append(row)

            writer.writerows(all)
    return send_file("C:\\Users\\RajnishKumarVENDORRo\\PycharmProjects\\CaseClassification\\outputfiles\\"+senders_list.filename,as_attachment=True)

@app.route('/mapping_dashboard')
@is_logged_in
def mapping_dashboard():
    return render_template('dailySentiment.html')


@app.route('/sentiment',methods=['GET', 'POST'])
@is_logged_in
def sentiment():
    #account_name = str(request.form['account'])
    senders_list = request.files['delivery_file']
    senders_location = secure_filename(senders_list.filename)
    if '.csv' in senders_list.filename.lower():
        senders_list.save(senders_location)
        csvfile1 = open(senders_location, 'rt')
    else:
        error = "Please pass a .csv file only"
        return render_template('dailySentiment.html', error=error)
    reader1 = csv.DictReader(csvfile1)
    resp =[]
    preparingData = []
    messagelist = []
    for row in reader1:
        try:
            casenumber = row['Case Number']
            account_name = row['Account Name: Account Name']
            casemessage = row['Body']
            if account_name:
                if row['Contact Name: Full Name'] == row['Created By: Full Name']:
                    person_type = "Customer"
                    #print(person_type, row['Body'], SentimentScore.predict(casemessage))
                    doc = {
                        'Case Number': casenumber,
                        'Account Name': account_name,
                        'Person Type': person_type,
                        'message': casemessage,
                        #'Score': SentimentScore.predict(casemessage)
                    }
                    messagelist.append([casemessage])
                    preparingData.append(doc)
        except:
            error = "Invalid File Format. The file doesn't contain Body field."
            return render_template('dailySentiment.html', error=error)
    try:
        i=0
        for data in SentimentScore.predict(messagelist):
            preparingData[i]['Score'] = data
            i+=1

    except:
        error = "Prediction limit exceeded for your current plan."
        return render_template('dailySentiment.html',error=error)
    #print(json.dumps(preparingData,indent=2))
    print(len(preparingData))
    csv_columns = ['Case Number', 'Account Name', 'Person Type', 'message', 'Score', 'Review', 'Correct/Incorrect']
    csv_file = r"C:\Users\RajnishKumarVENDORRo\PycharmProjects\CaseClassification\SentimentFile\score_"+senders_list.filename
    try:
        with open(csv_file, 'w',newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in preparingData:
                writer.writerow(data)
    except IOError:
        print("I/O error")
        error = "Error Generating Report File"
        return render_template('dailySentiment.html', recommended_resourse=preparingData,
                               file_name=senders_list.filename,error=error)
    return render_template('dailySentiment.html',recommended_resourse=preparingData,file_name=senders_list.filename,downloadFile = csv_file)

@app.route('/downloadFILE',methods = ['GET','POST'])
def downloadFILE():
    filename = str(request.form['file'])
    return send_file(filename,as_attachment=True)

@app.route('/account_dashboard')
@is_logged_in
def account_dashboard():
    return render_template('under_construction.html')


@app.route('/timespent_dashboard')
@is_logged_in
def timespent_dashboard():
    return render_template('under_construction.html')

'''
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
            if body[i]['person_type'] != 'IBM Employee':
                graphData.append([creation_date, NLUscore])
            other_info.append(body[i])
    return render_template('caseProfile.html',graphData=graphData,data = other_info)

'''
@app.route('/talk', methods=['GET', 'POST'])
@is_logged_in
def talk():
    session['message_content'] = None
    case_numbers = request.files.get('search')
    caselist = []
    if case_numbers is not None:
        senders_location = secure_filename(case_numbers.filename)
        if '.csv' in case_numbers.filename.lower():
            case_numbers.save(senders_location)
            csvfile1 = open(senders_location, 'rt')
        else:
            error = "Please pass a .csv file only"
            return render_template('Dashboard.html', error=error)
        reader1 = csv.DictReader(csvfile1)
        for row in reader1:
            try:
                casenumber = row['Case Number']
                if len(casenumber)>3:
                    #caselist.append(tuple([casenumber]))
                    caselist.append(casenumber)
            except:
                error = "Case Number Field Not available"
                return render_template('Dashboard.html', error=error)
    from_date = request.form['fromDate']
    print(from_date)
    print(case_numbers)
    #df = dao.getOpenCasesByRange(from_date=from_date,to_date=to_date)
    if len(caselist) == 0:
        df = dao.getOpenCasesByDate(from_date)
    else:
        df = dao.getOpenCasesByDateCase(from_date,tuple(caselist))
    if not df.empty:
        print(df.shape)
        #df['messageID'] = df.apply(lambda x: str(uuid.uuid1()), axis=1)
        df['LASTMODIFIEDDATE'] = df['LASTMODIFIEDDATE'].apply(lambda x: x.strftime('%Y-%m-%d'))
        df['BODY'] = df['BODY'].apply(lambda x: correctString(x))
        toBeScored = df['BODY'].apply(lambda x: [x])
        df['score'] =[x for x in SentimentScore.predict(toBeScored.tolist())]
        dictDF = df.to_dict(orient='records')
        session['Content'] = dictDF
        print(len(dictDF))
        return render_template('Dashboard.html',data=dictDF)
    else:
        error = "No Data Available for the given date."
        return render_template('Dashboard.html', error=error)



@app.route('/message_review/<string:message_id>', methods=['POST'])
@is_logged_in
def message_review(message_id):
    print(message_id)
    response = request.form['response']
    remark = request.form['remarks']
    somedata = session['Content']
    print(len(somedata))
    print(somedata[0])
    for data in somedata:
        if data['ID'] == message_id:
            doc = data
            doc['ReviewerName'] =session['username']
            doc['ReviewDate']= datetime.datetime.today().strftime('%Y-%m-%d')
            doc['Remarks'] = remark
            doc['state'] = response
            if dao.upsertreview(doc):
                somedata.remove(data)
            break
    print(remark)
    print(response)
    print(type(somedata))
    return render_template('Dashboard.html',data=somedata)


@app.route('/reviewedmessagetab')
@is_logged_in
def reviewedmessagetab():
    return render_template('ReviewedMessages.html')

@app.route('/reviewed', methods=['GET', 'POST'])
@is_logged_in
def reviewed():
    from_date = request.form['fromDate']
    print(from_date)
    df = dao.getReviewedMessagesByDate(from_date)
    if not df.empty:
        print(df.shape)
        dictDF = df.to_dict(orient='records')
        print(len(dictDF))
        return render_template('ReviewedMessages.html',data=dictDF)
    else:
        error = "No Data Available for the given date."
        return render_template('ReviewedMessages.html', error=error)

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
