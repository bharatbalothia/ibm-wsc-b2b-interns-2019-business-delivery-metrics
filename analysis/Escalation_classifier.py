import json
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_classifier_v1 import *


natural_language_classifier = NaturalLanguageClassifierV1(
    iam_apikey='yJn4pwHJkf0XBX4VWSclhr-x2bmsfArP0vw7p5Uq4Rjq',
    url='https://gateway.watsonplatform.net/natural-language-classifier/api')


def watsonClassifer(data):
    classes = natural_language_classifier.classify_collection('1dbc1fx505-nlc-708', [{'text':data}]).get_result()
    return classes['collection'][0]['top_class']