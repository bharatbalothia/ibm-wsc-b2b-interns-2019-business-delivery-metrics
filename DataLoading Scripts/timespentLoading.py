import ibm_db
import pandas as pd
import ibm_db_dbi
import csv
import os

conn_db = ibm_db.connect("DATABASE=SFA;HOSTNAME=9.30.161.135;PORT=50001;PROTOCOL=TCPIP;UID=db2inst1;PWD=db@inst!;", "", "")
conn = ibm_db_dbi.Connection(conn_db)
pd.set_option('display.max_colwidth', -1)

typereport_base_dir = "../reports/timespent"
left_files = "/left"
done_files = "/done"
log_file = "logfile.txt"

logfile = open(os.path.join(typereport_base_dir, log_file),'w+')

columns = "CaseNumber, SessionTimeSupportAgentObfuscatedName, CaseSupportMission, SESSIONTIMEBUSINESSUNIT, SESSIONTIMEDATECREATED, TOTALDURATION "

placeholders = ', '.join(['?'] * len(columns.split(",")))
insert_sql = "INSERT INTO actual_timespent ( " + columns + ") VALUES ( " + placeholders + ")"
stmt_insert = ibm_db.prepare(conn_db, insert_sql)

issueflag = 0


for filename in os.listdir(typereport_base_dir+left_files):
    if filename.endswith(".csv"):
        #print(os.path.join(directory, filename))
        report = os.path.join(typereport_base_dir+left_files, filename)
        csvfile1 = open(report,  'rt',encoding='latin1')
        index=1
        reader1 = csv.DictReader(csvfile1)
        for row in reader1:
            valueData = [row['Case Number'],row['Session Time Support Agent Obfuscated Name'],row['Case Support Mission'],row['Session Time Business Unit'],
                         row[' Session Time Date Created'],row['Total Duration']]
            try:
                if len(row[' Session Time Date Created']) > 2:
                    ibm_db.execute(stmt_insert, tuple(valueData))
            except:
                #print("Transaction couldn't be completed:" , ibm_db.stmt_errormsg())
                logfile.write(
                    "File Name: {0} Failed to Insert row number {1}. DB2 gave this error: {2}\n".format(filename,
                                                                                                        str(index), str(
                            ibm_db.stmt_errormsg())))
                issueflag = 1
            else:
                print("sucessfully inserted " + str(index))
            index += 1
            print(report)
            csvfile1.close()
            os.rename(report, os.path.join(typereport_base_dir + done_files, filename))
        logfile.close()
