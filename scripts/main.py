from telebot import TeleBot

from etl import EcoBiciMap

ECOBICI_CLIENT_ID = '2199_132ley5lk3404wkk4c4w4ggo48kwcokosogg0k0www84s08gs'
ECOBICI_CLIENT_SECRET = '61xytd2ketssok44g4kkckwogkg048gk0ok48sc0k0wgc8scs'

TELEGRAM_API_KEY = '5424781174:AAGSCoHB5NXzsdRPPRR-9qXQ8VtuLhT8I34'
ZIPCODE = '06500'

ebm = EcoBiciMap(ECOBICI_CLIENT_ID, ECOBICI_CLIENT_SECRET, TELEGRAM_API_KEY, is_local=True)
ebm.get_token(first_time=True)
ebm.st = ebm.get_data()
ebm.av = ebm.get_data(availability=True)
ebm.get_shapefile()
print('Map ready!')

bot = TeleBot(TELEGRAM_API_KEY)
@bot.message_handler(commands=['zipcode'])
def send_map(message):
	ebm.transform(zipcode=ZIPCODE)
	img = ebm.plot_map(
		data=ebm.df,
		col_to_plot='bikes_proportion',
		img_name='map',
		padding=0.006,
		color='#ffffff',
		edgecolor='#00acee', 
		points_palette='Blues'
	)
	bot.send_photo(chat_id=message.chat.id, photo=img)

bot.infinity_polling()



#################################################################################
def stock_request(message):
  request = message.text.split()
  if len(request) < 2 or request[0].lower() not in "price":
    return False
  else:
    return True

@bot.message_handler(func=stock_request)
def send_price(message):
  request = message.text.split()[1]