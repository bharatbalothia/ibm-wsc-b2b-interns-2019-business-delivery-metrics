import ibm_db
import pandas as pd
import ibm_db_dbi

conn_db = ibm_db.connect("DATABASE=SFA;HOSTNAME=9.30.161.135;PORT=50001;PROTOCOL=TCPIP;UID=db2inst1;PWD=db@inst!;", "", "")
conn = ibm_db_dbi.Connection(conn_db)
pd.set_option('display.max_colwidth', -1)


def getOpenCasesByRange(from_date=None,to_date=None):
    sql = "select casenumber,date(to_date(LEFT(lastmodifieddate,length(lastmodifieddate)-2),'MM/DD/YYYY HH:MI')) as lastmodifieddate,id,accountname,CREATEDBYFULLNAME,body " \
          "from opencases where date(to_date(LEFT(lastmodifieddate,length(lastmodifieddate)-2),'MM/DD/YYYY HH:MI')) > " \
          "date('"+from_date+"') and date(to_date(LEFT(lastmodifieddate,length(lastmodifieddate)-2),'MM/DD/YYYY HH:MI')) < date('"+to_date+"')  and CREATEDBYFULLNAME=CONTACTNAMEFULLNAME "

    df = pd.read_sql(sql, conn)
    #print(df)
    return df

def getOpenCasesByDate(search_date=None):
    sql = "select casenumber,date(to_date(LEFT(lastmodifieddate,length(lastmodifieddate)-2),'MM/DD/YYYY HH:MI')) as lastmodifieddate,ID,accountname,CREATEDBYFULLNAME,body " \
          "from opencases where date(to_date(LEFT(lastmodifieddate,length(lastmodifieddate)-2),'MM/DD/YYYY HH:MI')) = " \
          "date('" + search_date + "') and CREATEDBYFULLNAME=CONTACTNAMEFULLNAME "
    df = pd.read_sql(sql, conn)
    # print(df)
    return df


def getOpenCasesByDateCase(search_date,caselist):
    sql = "select casenumber,date(to_date(LEFT(lastmodifieddate,length(lastmodifieddate)-2),'MM/DD/YYYY HH:MI')) as lastmodifieddate,ID,accountname,CREATEDBYFULLNAME,body " \
          "from opencases where date(to_date(LEFT(lastmodifieddate,length(lastmodifieddate)-2),'MM/DD/YYYY HH:MI')) = " \
          "date('" + search_date + "') and CREATEDBYFULLNAME=CONTACTNAMEFULLNAME and CASENUMBER in "+str(caselist)+""
    print(sql)
    df = pd.read_sql(sql, conn)
    # print(df)
    return df

def postReviews(reviewDoc):
    columns = ', '.join(reviewDoc.keys())
    placeholders = ', '.join(['?'] * len(reviewDoc))

    insert_sql = "INSERT INTO REVIEWEDMESSAGES ( " + columns + ") VALUES ( " + placeholders + ")"
    stmt_insert = ibm_db.prepare(conn_db, insert_sql)
    print(insert_sql)
    try:
        ibm_db.execute(stmt_insert, tuple(reviewDoc.values()))
    except:
        print("Transaction couldn't be completed:", ibm_db.stmt_errormsg())
        return False
    else:
        print("sucessfully inserted ")
        return True

def upsertreview(reviewDoc):
    sql = "MERGE INTO REVIEWEDMESSAGES AS mt USING ( SELECT * FROM TABLE ( VALUES "+ str(tuple(reviewDoc.values())) +" )) AS " \
        "vt( CASENUMBER, LASTMODIFIEDDATE, ID, ACCOUNTNAME, CREATEDBYFULLNAME, BODY, score, ReviewerName, ReviewDate, Remarks, state) ON (mt.ID = vt.ID)" \
        " WHEN MATCHED THEN UPDATE SET ReviewerName = vt.ReviewerName," \
                                "   state=vt.state, ReviewDate=vt.ReviewDate, Remarks=vt.Remarks  WHEN NOT MATCHED THEN INSERT " \
        "( CASENUMBER, LASTMODIFIEDDATE, ID, ACCOUNTNAME, CREATEDBYFULLNAME, BODY, score, ReviewerName, ReviewDate, Remarks, state) VALUES "+ str(tuple(reviewDoc.values())) +" "
    print(sql)
    try:
        ibm_db.exec_immediate(conn_db, sql)
    except:
        print("Transaction couldn't be completed:", ibm_db.stmt_errormsg())
        return False
    else:
        print("sucessfully inserted ")
        return True

def getReviewedMessagesByDate(search_date=None):
    sql = "select * from REVIEWEDMESSAGES where REVIEWDATE = date('"+search_date+"')"
    df = pd.read_sql(sql, conn)
    # print(df)
    return df