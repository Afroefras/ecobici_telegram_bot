from etl import EcoBiciMap
from telebot import TeleBot

# from os import getenv
# ECOBICI_CLIENT_ID = getenv('ECOBICI_CLIENT_ID')
# ECOBICI_CLIENT_SECRET = getenv('ECOBICI_CLIENT_SECRET')
# TELEGRAM_API_KEY = getenv('TELEGRAM_API_KEY')

ECOBICI_CLIENT_ID = '2199_132ley5lk3404wkk4c4w4ggo48kwcokosogg0k0www84s08gs'
ECOBICI_CLIENT_SECRET = '61xytd2ketssok44g4kkckwogkg048gk0ok48sc0k0wgc8scs'
TELEGRAM_API_KEY = '5424781174:AAGSCoHB5NXzsdRPPRR-9qXQ8VtuLhT8I34'


ebm = EcoBiciMap(ECOBICI_CLIENT_ID, ECOBICI_CLIENT_SECRET, is_local=True)
ebm.get_token(first_time=True)
ebm.st = ebm.get_data()
ebm.av = ebm.get_data(availability=True)
ebm.get_shapefile()
valid_districts = set(ebm.st['districtName'])
valid_zipcodes = set(ebm.st['zipCode'])
print('Map ready!')


bot = TeleBot(TELEGRAM_API_KEY)

@bot.message_handler(commands=['start'])
def test(message):
	bot.reply_to(message, 'EcobiciMapBot')


@bot.message_handler(commands=['colonias'])
def test(message):
	bot.reply_to(message, '\n'.join([str(x) for x in valid_districts]))

@bot.message_handler(commands=['zipcodes'])
def test(message):
	bot.reply_to(message, '\n'.join([str(x) for x in valid_zipcodes]))


def filter_zipcode(message):
	request = message.text.split()
	if request[0].lower()=='zipcode' and request[1] in valid_zipcodes: return True
	else: return False

@bot.message_handler(func=filter_zipcode)
def send_map(message):
	to_filter = message.text.split()[1]
	df = ebm.transform(filter_col='zipCode', filter_value=to_filter)
	img = ebm.plot_map(df, color='#ffffff', edgecolor='#00acee')
	bot.send_photo(chat_id=message.chat.id, photo=img)
	print(f'Sent CP: {to_filter}!')


def filter_district(message):
	request = message.text.split()
	district = ' '.join(request[1:])
	ebm.options_district = ebm.give_options(district, valid_districts, n=5, cutoff=0.6)
	if request[0].lower()[:3]=='col' and any(map(lambda x: x in valid_districts, ebm.options_district)): return True
	else: return False

@bot.message_handler(func=filter_district)
def send_map(message):
	bot.reply_to(message, 'Las opciones podrían ser:\n\n-'+'\n-'.join([str(x) for x in ebm.options_district]))
	# df = ebm.transform(zipcode=to_filter)
	# img = ebm.plot_map(df, color='#ffffff', edgecolor='#00acee')
	# bot.send_photo(chat_id=message.chat.id, photo=img)
	print(f'Sent options!')


bot.infinity_polling()
