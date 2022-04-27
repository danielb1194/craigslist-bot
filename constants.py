"""Constants and type definitions"""


from copyreg import constructor

from telegram import InlineKeyboardButton

# the conversation states
CHOOSE_STATE, CHOOSE_CITIES, KEYWORDS, CHOOSE_CATEGORY, REQUEST_PERIOD, CONFIRM_CITIES = range(
    6)


class Area:
    text: str
    value: str

    def __init__(self, text: str, value: str):
        self.text = text
        self.value = value

    def button(self):
        return InlineKeyboardButton(text=self.text, callback_data=self.value)

    def as_dict(self):
        return {'text': self.text, 'value': self.value}


class State(Area):
    cities: list = []

    def __init__(self, text: str, value: str, cities: list):
        self.text = text
        self.value = value
        self.cities = cities

    def button(self):
        return InlineKeyboardButton(text=self.value.upper(), callback_data=self.value)


STATES = {
    'tx': State('Texas', 'tx', [
        {'text': 'Houston', 'value': 'houston'},
        {'text': 'Austin', 'value': 'austin'},
        {'text': 'Dallas', 'value': 'dallas'},
        {'text': 'Albilene', 'value': 'abilene'},
        {'text': 'Amarillo', 'value': 'amarillo'},
        {'text': 'Beaumont', 'value': 'beaumont'},
        {'text': 'Brownville', 'value': 'brownville'},
        {'text': 'College Station', 'value': 'collegestation'},
        {'text': 'Corpus Christi', 'value': 'corpuschristi'}
    ]),
    'ca': State('California', 'ca', [
        {'text': 'San Francisco', 'value': 'sfbay'},
        {'text': 'San diego', 'value': 'sandiego'}
    ]),
    'tn': State('Tennessee', 'tn', [
        {'text': 'Nashville', 'value': 'nashville'},
        {'text': 'Clarksville', 'value': 'clarksville'},
        {'text': 'Memphis', 'value': 'memphis'},
        {'text': 'Knoxville', 'value': 'knoxville'}
    ]),
    'al': State('Alabama', 'al', [
        {'text': 'Huntsville / Decatur', 'value': 'huntsville'}
    ]),
    'ky': State('Kentucky', 'ky', [
        {'text': 'Eastern Kentucky', 'value': 'eastky'},
        {'text': 'Bowling Green', 'value': 'bgky'},
        {'text': 'Western Kentucky', 'value': 'westky'}
    ])
}

CRAIGSLIST_CATEGORIES = {
    'ata': 'antiques',
    'ppa': 'appliances',
    'ara': 'arts & crafts',
    'sna': 'atvs, utvs, snowmobiles',
    'pta': 'auto parts',
    'wta': 'auto wheels & tires',
    'ava': 'aviation',
    'baa': 'baby & kid stuff',
    'bar': 'barter',
    'bip': 'bicycle parts',
    'bia': 'bicycles',
    'bpa': 'boat parts & accessories',
    'boo': 'boats',
    'bka': 'books & magazines',
    'bfa': 'business',
    'cta': 'cars & trucks',
    'ema': 'cds / dvds / vhs',
    'moa': 'cell phones',
    'cla': 'clothing & accessories',
    'cba': 'collectibles',
    'syp': 'computer parts',
    'sya': 'computers',
    'ela': 'electronics',
    'gra': 'farm & garden',
    'zip': 'free stuff',
    'fua': 'furniture',
    'gms': 'garage & moving sales',
    'foa': 'general for sale',
    'haa': 'health and beauty',
    'hva': 'heavy equipment',
    'hsa': 'household items',
    'jwa': 'jewelry',
    'maa': 'materials',
    'mpa': 'motorcycle parts & accessories',
    'mca': 'motorcycles/scooters',
    'msa': 'musical instruments',
    'pha': 'photo/video',
    'rva': 'recreational vehicles',
    'sga': 'sporting goods',
    'tia': 'tickets',
    'tla': 'tools',
    'taa': 'toys & games',
    'tra': 'trailers',
    'vga': 'video gaming',
    'waa': 'wanted'
}
