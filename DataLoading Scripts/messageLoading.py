import ibm_db
import pandas as pd
import ibm_db_dbi
import csv
import os
import requests

conn_db = ibm_db.connect("DATABASE=SFA;HOSTNAME=9.30.161.135;PORT=50001;PROTOCOL=TCPIP;UID=db2inst1;PWD=db@inst!;", "",
                         "")
conn = ibm_db_dbi.Connection(conn_db)
pd.set_option('display.max_colwidth', -1)

typereport_base_dir = "../reports/message"
left_files = "\\left"
done_files = "\\done"
log_file = "logfile.txt"


logfile = open(os.path.join(typereport_base_dir, log_file), 'w+')

columns = 'CaseNumber, AccountName, OPENEDDATETIME, ContactNameFullName, CreatedByFullName, CaseOwnerFullName, CreatedDate, Body, Status, score'

placeholders = ', '.join(['?'] * len(columns.split(",")))
insert_sql = "INSERT INTO ACTUAL_MESSAGE ( " + columns + ") VALUES ( " + placeholders + ")"
stmt_insert = ibm_db.prepare(conn_db, insert_sql)


for filename in os.listdir(typereport_base_dir + left_files):
    if filename.endswith(".csv"):
        # print(os.path.join(directory, filename))
        report = os.path.join(typereport_base_dir + left_files, filename)
        dataFrame = pd.read_csv(report,encoding='latin1')
        messageList = dataFrame['Body'].tolist()
        resp = requests.post('http://9.199.145.49:12500/api/sentiment', json={"message":messageList}).json()
        scores = resp['scores']
        dataFrame['score'] = scores
        index=1
        for index,row in dataFrame.iterrows():
            valueData = [row['Case Number'],row['Account Name: Account Name'],row['Opened Date/Time'],row['Contact Name: Full Name'],row['Created By: Full Name'],row['Case Owner: Full Name'],row['Created Date'],row['Body'],row['Status'],row['score']]
            try:
                ibm_db.execute(stmt_insert, tuple(valueData))
            except:
                #print("Transaction couldn't be completed:" , ibm_db.stmt_errormsg())
                logfile.write("File Name: {0} Failed to Insert row number {1}. DB2 gave this error: {2}\n".format(filename,str(index), str(ibm_db.stmt_errormsg())))
                #issueflag = 1
            else:
                print("sucessfully inserted "+str(index))
            index+=1
