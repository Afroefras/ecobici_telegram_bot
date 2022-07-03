from etl import EcoBiciMap
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# from os import getenv
# ECOBICI_CLIENT_ID = getenv('ECOBICI_CLIENT_ID')
# ECOBICI_CLIENT_SECRET = getenv('ECOBICI_CLIENT_SECRET')
# TELEGRAM_API_KEY = getenv('TELEGRAM_API_KEY')

ECOBICI_CLIENT_ID = '2199_132ley5lk3404wkk4c4w4ggo48kwcokosogg0k0www84s08gs'
ECOBICI_CLIENT_SECRET = '61xytd2ketssok44g4kkckwogkg048gk0ok48sc0k0wgc8scs'
TELEGRAM_API_KEY = '5424781174:AAGSCoHB5NXzsdRPPRR-9qXQ8VtuLhT8I34'

district_col = 'districtName'
zipcode_col = 'zipcodeName'

# ETL del mapa en tiempo real
ebm = EcoBiciMap(ECOBICI_CLIENT_ID, ECOBICI_CLIENT_SECRET, is_local=True)
ebm.get_token(first_time=True)
ebm.st = ebm.get_data()
ebm.av = ebm.get_data(availability=True)
ebm.get_shapefile()
valid_districts = set(ebm.st[district_col].astype(str))
valid_zipcodes = set(ebm.st[zipcode_col].astype(str))
sorted_zipcodes = set(ebm.st[[district_col, zipcode_col]].astype(str).apply(':\t\t\t'.join, axis=1))
print('Map ready!')


# Instanciar TelegramBot
bot = TeleBot(TELEGRAM_API_KEY)

# Instrucciones de uso
@bot.message_handler(commands=['start','help'])
def test(message):
	bot.reply_to(message, 'EcobiciMapBot')


# Consultar las colonias y/o códigos postales disponibles
@bot.message_handler(commands=['colonias'])
def test(message):
	bot.reply_to(message, '\n'.join(sorted(valid_districts)))
@bot.message_handler(commands=['zipcodes'])
def test(message):
	bot.reply_to(message, '\n'.join(sorted(sorted_zipcodes)))


# Mapa para el código postal indicado
def filter_zipcode(message):
	request = message.text.split()
	if request[0].lower()==zipcode_col and request[1] in valid_zipcodes: return True
	else: return False
@bot.message_handler(func=filter_zipcode)
def send_map(message):
	zipcode = message.text.split()[1]
	df = ebm.transform(filter_col=zipcode_col, filter_value=zipcode)
	if df.shape[0] == 0: bot.reply_to(message, f'Código postal: {zipcode} no cuenta con información disponible')
	else:
		img = ebm.plot_map(df, color='#ffffff', edgecolor='#00acee')
		bot.reply_to(message, f'Código Postal {zipcode}:')
		bot.send_photo(chat_id=message.chat.id, photo=img)
		print(f'Sent CP: {zipcode}!')


# Mapa para la colonia cuando la consulta del usuario devuelve sólo una opción
def district_clear(message):
	request = message.text.split()
	if request[0].lower()[:3]=='col':
		district = ' '.join(request[1:])
		ebm.district_options = ebm.give_options(district, valid_districts, n=4, cutoff=0.6)
		if len(ebm.district_options)==1: return True
		else: return False
	else: return False
@bot.message_handler(func=district_clear)
def send_map(message):
	district = ebm.district_options[0]
	df = ebm.transform(filter_col=district_col, filter_value=district)
	img = ebm.plot_map(df, color='#ffffff', edgecolor='#00acee')
	bot.reply_to(message, f'Colonia {district}:')
	bot.send_photo(chat_id=message.chat.id, photo=img)
	print(f'Sent map of {district}!')


# Mapa para la colonia cuando la consulta del usuario devuelve más de una opción
def district_not_clear(message):
	request = message.text.split()
	if request[0].lower()[:3]=='col':
		district = ' '.join(request[1:])
		ebm.district_options = ebm.give_options(district, valid_districts, n=4, cutoff=0.6)
		if len(ebm.district_options) > 1: return True
		else: return False
	else: return False
@bot.message_handler(func=district_not_clear)
def send_options_then_map(message):
	bot.reply_to(message, 'Las opciones podrían ser:\n\n-'+'\n-'.join([str(x) for x in ebm.district_options]))
	markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=False, one_time_keyboard=True)
	for district_option in ebm.district_options:
		markup.add(KeyboardButton(f'Colonia {district_option}'))
	bot.send_message(message.chat.id, "¿Qué colonia quieres ver?", reply_markup=markup)

bot.infinity_polling()
