from etl import EcoBiciMap
from telebot import TeleBot, formatting
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# from os import getenv
# ECOBICI_CLIENT_ID = getenv('ECOBICI_CLIENT_ID')
# ECOBICI_CLIENT_SECRET = getenv('ECOBICI_CLIENT_SECRET')
# TELEGRAM_API_KEY = getenv('TELEGRAM_API_KEY')

ECOBICI_CLIENT_ID = '2199_132ley5lk3404wkk4c4w4ggo48kwcokosogg0k0www84s08gs'
ECOBICI_CLIENT_SECRET = '61xytd2ketssok44g4kkckwogkg048gk0ok48sc0k0wgc8scs'
TELEGRAM_API_KEY = '5424781174:AAGSCoHB5NXzsdRPPRR-9qXQ8VtuLhT8I34'

district_col = 'districtName'
zipcode_col = 'zipCode'

# ETL del mapa en tiempo real
ebm = EcoBiciMap(ECOBICI_CLIENT_ID, ECOBICI_CLIENT_SECRET, is_local=True)
ebm.get_token(first_time=True)
ebm.st = ebm.get_data()
ebm.av = ebm.get_data(availability=True)
ebm.get_shapefile()
valid_districts = set(ebm.st[district_col].astype(str))
valid_zipcodes = set(ebm.st[zipcode_col].astype(str))
print('Map ready!')


# Instanciar TelegramBot
bot = TeleBot(TELEGRAM_API_KEY)

# Instrucciones de uso
@bot.message_handler(commands=['start','help'])
def test(message):
	bot.send_message(
		message.chat.id,
		'''
		Hola! Soy EcobiciMapBot V1.0 y aquí puedes consultar qué tantas bicis hay disponibles en CDMX 🚴🏾‍♀️🚴🏾‍♂️
		\n¿Quieres ver este tutorial de nuevo? Sólo tienes que mandar /help 

		\nAhora sí, las instrucciones son simples:
		\n\t- /todo         Disponibilidad en CDMX
		\n\t- /colonias     Lista de colonias disponibles
		\n\t- /colonias     Lista de códigos postales disponibles
		'''
	)


# Consultar las colonias y/o códigos postales disponibles
@bot.message_handler(commands=['colonias'])
def districts_info(message):
	districts, zipcodes = ebm.show_grouped(ebm.st, to_group=district_col, to_agg=zipcode_col)
	bot.reply_to(
		message, 
		'''Las colonias disponibles (y sus códigos postales) son: \n - 
		''' + '\n - '.join(map(lambda x: f'{x[0]}:   {x[-1]}', zip(districts, zipcodes))))
@bot.message_handler(commands=['zipcodes'])
def zipcodes_info(message):
	zipcodes, districts = ebm.show_grouped(ebm.st, to_group=zipcode_col, to_agg=district_col)
	bot.reply_to(
		message, 
		'''Los códigos postales disponibles (y las colonias que engloban) son:
	 	- ''' + '\n - '.join(map(lambda x: f'{x[0]}:   {x[-1]}', zip(zipcodes, districts))))


# Consulta todo el mapa
@bot.message_handler(commands=['todo'])
def full_map(message):
	df = ebm.transform()
	img = ebm.plot_map(df, color='#ffffff', edgecolor='#00acee')
	bot.reply_to(message, 'Disponibilidad en vivo:')
	bot.send_photo(chat_id=message.chat.id, photo=img)
	print('Map sent!')


# Mapa para el código postal indicado
def filter_zipcode(message):
	request = message.text.split()
	if request[0].lower()=='zipcode' and request[1] in valid_zipcodes: return True
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
		print(f'CP: {zipcode} sent!')


# Mapa para la colonia cuando la consulta del usuario devuelve sólo una opción
def district_clear(message):
	request = message.text.split()
	if request[0].lower()[:3]=='col':
		district = ' '.join(request[1:])
		ebm.district_options = ebm.give_options(district, valid_districts, max_options=1, n=1, cutoff=0.6)
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
	print(f'{district} map sent!')


# Mapa para la colonia cuando la consulta del usuario devuelve más de una opción
def district_not_clear(message):
	request = message.text.split()
	if request[0].lower()[:3]=='col':
		district = ' '.join(request[1:])
		ebm.district_options = ebm.give_options(district, valid_districts, max_options=5, n=5, cutoff=0.6)
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
