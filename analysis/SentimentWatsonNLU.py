import json
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, CategoriesOptions, SentimentOptions

natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2018-11-16',
    iam_apikey='28K1m-tr3wXzozHs-PzDy8QgQF9C7c133UrZAuJjrxsY',
    url='https://gateway.watsonplatform.net/natural-language-understanding/api'
)


def watsonNLU(analyse_this):
    response = natural_language_understanding.analyze(
        text=analyse_this,
        features=Features(sentiment=SentimentOptions())).get_result()

    return str(response['sentiment']['document']['score']), response['sentiment']['document']['label']
