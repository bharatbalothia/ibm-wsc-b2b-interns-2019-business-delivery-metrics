import urllib3, requests, json

sentence = "thanks but this is not good"

# retrieve your wml_service_credentials_username, wml_service_credentials_password, and wml_service_credentials_url from the
# Service credentials associated with your IBM Cloud Watson Machine Learning Service instance

#sunil's wml creds
#wml_credentials={
#"url": "https://eu-gb.ml.cloud.ibm.com",
#"username": "f09d09eb-68f7-4a39-9bc7-cdac304026fd",
#"password": "0df121f0-ac43-423b-abe6-fbb7264d5c3a"
#}

#robin's wml creds
#wml_credentials={
#"url": "https://us-south.ml.cloud.ibm.com",
#"username": "981947f3-fc46-4a38-8d1a-2a5d429097f5",
#"password": "3384e899-f47c-4000-bb92-e258a21e66ce"
#}


#rajan wml creds
wml_credentials={
"url": "https://us-south.ml.cloud.ibm.com",
"username": "ff914608-0372-41e3-a91c-16827a07f42e",
"password": "6edd3ec6-ad95-4669-8521-78239936a02a"
}

headers = urllib3.util.make_headers(basic_auth='{username}:{password}'.format(username=wml_credentials['username'], password=wml_credentials['password']))
url = '{}/v3/identity/token'.format(wml_credentials['url'])
response = requests.get(url, headers=headers)
mltoken = json.loads(response.text).get('token')

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}

# NOTE: manually define and pass the array(s) of values to be scored in the next line
payload_scoring = {"fields": ["review"], "values": [[sentence]]}


#this Deployment is from rajan's wml credentials
response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/v3/wml_instances/ddfe31f9-1825-4820-a5b6-ba68232e2b2a/deployments/c02b3a9e-ca14-48f2-9d5b-1d815aee578b/online', json=payload_scoring, headers=header)
#this Deployment is from robin's wml credentials
#response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/v3/wml_instances/913df54e-4ddc-488d-baa2-36fedc75aaa6/deployments/1e0325c9-0167-4ad4-8bc9-202ed7ecbdbf/online', json=payload_scoring, headers=header)

##these Deployment is from sunils's wml credentials
#response_scoring = requests.post('https://eu-gb.ml.cloud.ibm.com/v3/wml_instances/6e4b0a80-e71b-4b8f-903b-9baaafd0f889/deployments/0fd2d5c7-dae1-4ce7-9daa-33eb2143941f/online', json=payload_scoring, headers=header)
#response_scoring = requests.post('https://eu-gb.ml.cloud.ibm.com/v3/wml_instances/6e4b0a80-e71b-4b8f-903b-9baaafd0f889/deployments/a4732cb0-61c9-418e-8af3-2dbc91dd52a5/online', json=payload_scoring, headers=header)
prediction = json.loads(response_scoring.text)

def predicted_score(prediction):
    resultvalue = prediction['values'][0][0]
    if resultvalue ==1:
        value_scored = -(prediction['values'][0][1][1])
    else:
        value_scored = (prediction['values'][0][1][0])
    #print(value_scored)
    return value_scored



def predict(sentance):
    payload_scoring = {"fields": ["review"], "values": sentance}
    response_scoring = requests.post(
        'https://us-south.ml.cloud.ibm.com/v3/wml_instances/ddfe31f9-1825-4820-a5b6-ba68232e2b2a/deployments/c02b3a9e-ca14-48f2-9d5b-1d815aee578b/online',
        json=payload_scoring, headers=header)
    prediction = json.loads(response_scoring.text)
    print(prediction)
    for data in list(prediction['values']):
        resultvalue = data[0]
        # print(data)
        if resultvalue == 1:
            value_scored = -(data[1][1])
        else:
            value_scored = (data[1][0])
        # print(value_scored)
        yield "{0:.4f}".format(value_scored)
    #return predicted_score(prediction)