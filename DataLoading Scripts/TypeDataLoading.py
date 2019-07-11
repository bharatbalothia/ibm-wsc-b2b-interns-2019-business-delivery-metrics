import ibm_db
import pandas as pd
import ibm_db_dbi
import csv
import os

conn_db = ibm_db.connect("DATABASE=SFA;HOSTNAME=9.30.161.135;PORT=50001;PROTOCOL=TCPIP;UID=db2inst1;PWD=db@inst!;", "",
                         "")
conn = ibm_db_dbi.Connection(conn_db)
pd.set_option('display.max_colwidth', -1)

typereport_base_dir = "../reports/type"
left_files = "\\left"
done_files = "\\done"
log_file = "logfile.txt"

logfile = open(os.path.join(typereport_base_dir, log_file), 'w+')

columns = 'SUBJECT, CASEOWNER, CASENUMBER, ACCOUNTNAME, CASESUBJECT, SEVERITYLEVEL, TYPE, CASESTATUS, COMMENTS, ' \
          'ADDITIONALCOMMENTS, LASTMODIFIEDDATE, SUPPORTMISSION, CREATEDDATE '

placeholders = ', '.join(['?'] * len(columns.split(",")))
insert_sql = "INSERT INTO type1 ( " + columns + ") VALUES ( " + placeholders + ")"
stmt_insert = ibm_db.prepare(conn_db, insert_sql)

issueflag = 0

for filename in os.listdir(typereport_base_dir + left_files):
    if filename.endswith(".csv"):
        # print(os.path.join(directory, filename))
        report = os.path.join(typereport_base_dir + left_files, filename)
        csvfile1 = open(report, 'rt', encoding='latin1')
        index = 1
        reader1 = csv.DictReader(csvfile1)
        for row in reader1:
            valueData = [row['Subject'], row['Case Owner'], row['Case Number'], row['Account Name Text'],
                         row['Case Subject'], row['Severity Level'], row['Type'], row['Case Status'], row['Comments'],
                         row['Additional Comments'], row['Last Modified Date'],
                         row['Support Mission: Support Mission Name'], row['Case: Created Date/Time']]
            try:
                sql = "MERGE INTO type1 AS mt USING ( SELECT * FROM TABLE ( VALUES " + str(
                    tuple(valueData)) + " )) AS " \
                                        "vt( " + columns + ") ON (mt.CaseNumber = vt.CaseNumber)" \
                                                           " WHEN MATCHED THEN UPDATE SET LASTMODIFIEDDATE = vt.LASTMODIFIEDDATE," \
                                                           " COMMENTS=vt.COMMENTS, ADDITIONALCOMMENTS =vt.ADDITIONALCOMMENTS WHEN NOT MATCHED THEN INSERT " \
                                                           "(  " + columns + " ) VALUES " + str(tuple(valueData)) + " "
                print(sql)
                ibm_db.exec_immediate(conn_db, sql)
                #ibm_db.execute(stmt_insert, tuple(valueData))
            except:
                # print("Transaction couldn't be completed:" , ibm_db.stmt_errormsg())
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
