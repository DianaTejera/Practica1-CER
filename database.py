import pymongo
import datetime
from datetime import date
from werkzeug.security import check_password_hash
from urllib.request import urlopen
import re
import requests

#devuelve True si se registro
def registro(email, username, password, medialocal, mediaremoto):
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["usuarios"]
	usuario = {"username":username, "email":email, "clave":password, "mediaslocal":medialocal, "mediasremoto":mediaremoto}
	x = mycol.insert_one(usuario)
	return True


#Devuelve True si se logueo
#devuelve False si no esta registrado
def login(username, password):
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["usuarios"]
	myquery = {"username":username}
	mydoc = mycol.find_one(myquery)
	if mydoc:
		comprobacion = check_password_hash(mydoc["clave"], password)
		if comprobacion:
			return True
		else:
			return False
	else:
		return False


def registrado(email):
# Mira en la base de datos local si el email que se ha insertado ya tiene cuenta
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["usuarios"]
	myquery = {"email":email}
	mydoc = mycol.find_one(myquery)
	if mydoc:
		return True
	else:
		return False


def bbdd_medialocal(usuario):
# Da la media de los datos en la bbdd local
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["cambios"]
	valores = 0
	for ind in mycol.find():
		valores = valores + ind.get("valor")
	num_valores = mycol.count_documents({})
	media = valores / num_valores
	return media


def bbdd_mediaremoto(usuario):
# Da la media de los datos de la bbdd remota
# Primero, encontramos cuantos valores tiene guardados la base de datos online
	url = 'https://api.thingspeak.com/channels/1914797/feeds.json?api_key=17M98W451RDIWU7V&results=1'
	resp = requests.get(url)
	html = resp.text
	pattern = '"last_entry_id":(\d+)'
	match = re.search(pattern, html)
	valor = float(match.group(1))
	url = url + str(valor)
# Ahora, vamos encontrando todas las coincidencias de cambios para irlos sumandos y asi calcular la media
	resp = requests.get(url)
	html = resp.text
	pattern = re.compile('(field1":")(\d.\d+)')
	valores = 0
	for match in pattern.finditer(html):
		coincidencia = float(match.group(2))
		valores = valores + coincidencia
	media = valores / valor
	return media


def obtener_numero_medias_local(usuario, pedida_local):
# Devuelve el numero de medias que haya pedido el usuario de forma local
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["usuarios"]
	myquery = {"username":usuario}
	mydoc = mycol.find_one(myquery)
	if mydoc:
		if pedida_local == 1:
			media_anterior_local = mydoc.get("mediaslocal")
			nueva_media_local = media_anterior_local + 1
			mycol.update_one({"mediaslocal":media_anterior_local}, {"$set":{"mediaslocal":nueva_media_local}})
			return nueva_media_local
		else:
			media_ant_local = mydoc.get("mediaslocal")
			return media_ant_local


def obtener_numero_medias_remoto(usuario, pedida_remoto):
# Devuelve el numero de medias que haya pedido el usuario de forma remota
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["usuarios"]
	myquery = {"username":usuario}
	mydoc = mycol.find_one(myquery)
	if mydoc:
		if pedida_remoto == 1:
			media_anterior_remoto = mydoc.get("mediasremoto")
			nueva_media_remoto = media_anterior_remoto + 1
			mycol.update_one({"mediasremoto":media_anterior_remoto}, {"$set":{"mediasremoto":nueva_media_remoto}})
			return nueva_media_remoto
		else:
			media_ant_remoto = mydoc.get("mediasremoto")
			return media_ant_remoto


def obtener_umbral_historico(umbralhistorico):
# Devuelve los cinco ultimos datos por encima del umbral que ha solicitado el usuario
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["cambios"]
	valores = []
	tiempo = []
	fecha = []
	for ind in mycol.find():
		valor = ind.get("valor")
		umbralhistorico = float(umbralhistorico)
		if valor > umbralhistorico:
			time = ind.get("hora")
			date = ind.get("fecha")
			valores.append(valor)
			tiempo.append(time)
			fecha.append(date)
	num_valores = len(valores)
	if num_valores > 5:
		umbral_historico = valores[num_valores-5:num_valores]
		tiempos = tiempo[num_valores-5:num_valores]
		fechas = fecha[num_valores-5:num_valores]
		return umbral_historico, tiempos, fechas
	if num_valores == 0:
		umbral_historico = 0
		tiempos = 0
		fechas = 0
		return umbral_historico, tiempos, fechas
	if num_valores <= 5:
		umbral_historico = valores
		tiempos = tiempo
		fechas = fecha
		return umbral_historico, tiempos, fechas


def insertar_cambio_internet(valor):
	url = 'https://api.thingspeak.com/update?api_key=XZMJF11O64KBRTAI&field1='
	url = url + str(valor)
	with urlopen(url) as response:
		body = response.read()


def insertar_cambio(valor):
	myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
	mydb = myclient["practica"]
	mycol = mydb["cambios"]
	now = datetime.datetime.now()
	hora = str(now.hour+2) + ":" + str(now.minute)
	today = date.today()
	fecha = today.strftime("%d/%m/%Y")
	cambio = {"valor":valor, "hora":hora, "fecha":fecha}
	x = mycol.insert_one(cambio)
	return True
