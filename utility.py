import datetime


def try_parsing_date(text):
    for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    else:
        raise ValueError('no valid date format found')


def correctString(input_string):
    input_string = input_string.replace(".  ", ".").replace("&nbsp;"," ").replace('<p>',"").replace('</p>'," ")
    return (input_string[:2040] + '..') if len(input_string) > 2040 else input_string


