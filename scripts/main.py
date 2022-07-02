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
valid_zipcodes = set(ebm.st['zipCode'])
print('Map ready!')


bot = TeleBot(TELEGRAM_API_KEY)

@bot.message_handler(commands=['test'])
def test(message):
	bot.reply_to(message, message.text)



def filter_zipcode(message):
  request = message.text.split()
  if request[0].lower()=='zipcode' and request[1] in valid_zipcodes: return True
  else: return False

@bot.message_handler(func=filter_zipcode)
def send_map(message):
	to_filter = message.text.split()[1]
	df = ebm.transform(zipcode=to_filter)
	img = ebm.plot_map(df, color='#ffffff', edgecolor='#00acee')
	bot.send_photo(chat_id=message.chat.id, photo=img)
	print(f'Sent CP: {to_filter}!')


'''
Polanco             43
Roma Norte          37
Centro              30
Del Valle Centro    29
Juárez              27
'''



bot.infinity_polling()
