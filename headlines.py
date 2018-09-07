import feedparser
import datetime
import json
import urllib.parse
import urllib.request
from flask import Flask, render_template, request, make_response

app = Flask(__name__)

RSS_FEEDS = {
    'bbc': 'http://feeds.bbci.co.uk/news/rss.xml',
    'cnn': 'http://rss.cnn.com/rss/edition.rss',
    'fox': 'http://feeds.foxnews.com/foxnews/latest',
    'iol': 'http://www.iol.co.za/cmlink/1.640'
}

DEFAULTS = {
    'publication': 'bbc',
    'city': 'London',
    'currency_from': 'GBP',
    'currency_to': 'USD'
}

WEATHER_URL = \
    "http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&APPID=69be3ee79cc5d10c10b86facce4e02fe"
CURRENCY_URL = \
    "https://openexchangerates.org//api/latest.json?app_id=a6fed90be11f4dc7b68899f2c2b4d3cd"


def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)

    return DEFAULTS[key]


@app.route('/')
def home():
    # customized headlines based on user inputs or defaults..
    publication = get_value_with_fallback('publication')
    articles = get_news(publication)

    # customized weather based on user inputs or defaults..
    city = get_value_with_fallback('city')
    weather = get_weather(city)

    # get customized currency based on user input or default ..
    currency_from = get_value_with_fallback('currency_from')
    currency_to = get_value_with_fallback('currency_to')
    rate, currencies = get_rate(currency_from, currency_to)

    # save cookies and return templates ..
    response = make_response(render_template('home.html',
                                             articles=articles,
                                             weather=weather,
                                             currency_from=currency_from,
                                             currency_to=currency_to,
                                             rate=rate,
                                             currencies=sorted(currencies))
                             )
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie('publication', publication, expires=expires)
    response.set_cookie('city', city, expires=expires)
    response.set_cookie('currency_form', currency_from, expires=expires)
    response.set_cookie('currency_to', currency_to, expires=expires)

    return response


def get_news(query):
    if not query or not query.lower() in RSS_FEEDS:
        publication = DEFAULTS['publication']
    else:
        publication = query.lower()
    feed = feedparser.parse(RSS_FEEDS[publication])
    articles = feed['entries']

    return articles


def get_weather(query):
    api_url = WEATHER_URL
    query = urllib.parse.quote(query)
    url = api_url.format(query)
    data = urllib.request.urlopen(url).read()
    parsed = json.loads(data)
    weather = None
    if parsed.get('weather'):
        weather = {"description": parsed["weather"][0]["description"],
                   "temperature": parsed["main"]["temp"],
                   "city": parsed["name"],
                   "country": parsed["sys"]["country"]
                   }
    return weather


def get_rate(frm, to):
    all_currency = urllib.request.urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())

    return (to_rate / frm_rate, parsed.keys())


if __name__ == '__main__':
    app.run(port=8000, debug=True)
