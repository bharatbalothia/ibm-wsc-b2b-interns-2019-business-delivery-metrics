import datetime


def try_parsing_date(text):
    for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def correctString(input_string):
    return input_string.replace(".  ", ".").replace("&nbsp;"," ")