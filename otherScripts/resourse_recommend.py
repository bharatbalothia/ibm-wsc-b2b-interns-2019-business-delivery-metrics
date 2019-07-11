import json
import csv
from difflib import SequenceMatcher

resourcemap = "resourcemappingdone.csv"

csvfile1 = open(resourcemap,'rt')
reader1 = csv.DictReader(csvfile1)

resourse ={}

for row in reader1:
    resourse[row['Email ID']] = row['Mapped_Name']

resourse_file = "resourse_profile1.csv"

csvfile1 = open(resourse_file,'rt')
reader1 = csv.DictReader(csvfile1)

account ={}

typedict  = {
  "S - Map Change": "MCR",
  "S - Map Research": "MCR",
  "S - PER - New Map": "MCR",
  "S - PER - Map Change": "MCR",
  "S - Mapping Request": "MCR",
  "S - Code List Update": "MCR",
  "S - Project - New Map": "MCR",
  "S- PER- New Map": "MCR",
  "S - PER - parent request": "PER IMPLEMENTATION",
  "S - PER - New TP": "PER IMPLEMENTATION",
  "S - PER - Communication": "PER IMPLEMENTATION",
  "S - PER - Other": "PER IMPLEMENTATION",
  "S - Configuration changes": "PER IMPLEMENTATION"
}

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

for row in reader1:
    doc = {
            "Resourse_id" : resourse[row['User_id']] if row['User_id'] in resourse else row['User_id'],
            "Appreciations count" : int(row['Appreciations count']),
            "Escalation count" : int(row['Escalation count']),
            "Resource Type": row['TYPE'],
            "Status" : row['Status']
            }
    if row['Clients'] in account:
        account[row['Clients']].append(doc)
    else:
        account[row['Clients']] = [doc]

for key in account:
    account[key] = sorted(account[key], key = lambda i: (-i['Escalation count'],i['Appreciations count']),reverse=True)

#print(json.dumps(account,indent=2))
#for key in account:
#    print(key)
'''
while True:
    account_search = input("Please Enter an account Name:")
    account_search = account_search.strip()
    if account_search in account and len(account[account_search]) >2:
        print(json.dumps([account[account_search][0],account[account_search][1]],indent=2))
    elif account_search in account and len(account[account_search]) <2:
        print(json.dumps([account[account_search][0]],indent=2))
    else:
        print("Account not avilable")

'''
clientList = [x for x in account]
typelist = [x for x in typedict]
resource_not_consider = ["Raghavendra KrishnaMurthy"]


def recommend(account_search,casetype):
    account_ser = ""
    caset = ""
    for data in clientList:
        if similar(account_search, data) > 0.8:
            account_ser = data
            break
    for data in typelist:
        if similar(casetype, data) > 0.8:
            caset =  typedict[data]
            break
    #return account[account_search]
    resp = []
    if account_ser in account:
        for data in account[account_ser]:
            if data['Resource Type'] == caset and data['Status'] == "Avilable" and data['Resourse_id'] not in resource_not_consider:
                resp.append(data)
            if len(resp) == 2:
                return resp
            else:
                continue
    return resp
    '''
    if len(account[account_search]) > 2:
        return [account[account_search][0], account[account_search][1]]
    elif len(account[account_search]) < 2:
        return [account[account_search][0]]
    '''

def account_list():
    account_list = []
    for key in account:
        account_list.append(key)
    return account_list

# some Accounts to test
# 'Highbury Canco Corporation' 'CEVA Logistics US, Inc.'  'HENDRICKSON USA, LLC' "Tesla Motors" "PEG PEREGO U.S.A., INC." "Lindt & Sprungli" "Polycom, Inc." "ArvinMeritor Inc (MI)"
