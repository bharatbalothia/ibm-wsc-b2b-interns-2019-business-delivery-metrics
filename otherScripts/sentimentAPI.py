from flask import Flask, request, jsonify
import pickle


app = Flask(__name__)


modelfile = 'finalized_model.sav'
loaded_model = pickle.load(open(modelfile, 'rb'))

def sentiScore(messageList):
    Ypredict = loaded_model.predict_proba(messageList)
    scores = []
    for record in Ypredict:
        if record[0] > record[1]:
            scores.append(record[0])
        else:
            scores.append(-record[1])
    return scores

@app.route('/api/sentiment', methods=['GET', 'POST'])
def add_message():
    content = request.json
    messagelist = content['message']
    scorelist = sentiScore(messagelist)
    resp = {"scores": scorelist}
    return jsonify(resp)

if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)


'''
import requests
requests.post('http://localhost:5000/api/sentiment', json={"message":["This is a bad one","This is good"]}).json()
'''