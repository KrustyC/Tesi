#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import urlopen
import json
import sys
from urllib2 import HTTPError
import dbScraping

from clustering import training_set_db, sensquare_db
from pyxdameraulevenshtein import damerau_levenshtein_distance

from datetime import datetime, timedelta
import requests

keyArray = ['description', 'elevation', 'name', 'created_at', 'updated_at', 'longitude', 'latitude', 'last_entry_id', 'id', 'tags', 'metadata', 'url']

training_db = training_set_db.MyDB()
sensquare = sensquare_db.MyDB()


training_set = training_db.get_training_set_relevant_streams()

dictionary = {'Temperature': [], 'Dust_Level': [], 'Gas_Level': [],'Brightness': [], 'Power': [], 'UV': [],'Heat_Index': [],
              'Pressure': [], 'Rain_Index': [], 'Radiation': [],'Humidity': [], 'Wind_Direction': [], 'Wind_Speed': []}

classes_to_id = {
	'Temperature' : 'TEMP',
	'Dust_Level': 'DUST',
	'Gas_Level': 'GASL',
	'Brightness': 'BRTH',
	'Power':'POWR',
	'UV':'UV',
	'Heat_Index':'HTIX',
	'Pressure': 'PRES' ,
	'Rain_Index': 'RAIN',
	'Radiation': 'RADI',
	'Humidity': 'HUMY',
	'Wind_Direction': 'WIDR',
	'Wind_Speed': 'WISP'
}


# Here we fill the dictionary with the training set plus preprocessing (lowercase and whitespaces)
def fill_dictionary():    
    for stream in training_set:
        classe = stream["field_class"]
        field = stream["field_name"]
        dictionary[classe].append(field.strip().replace(' ', '_'))

def trim_string(string):
	string = string.replace('"','')
	string = string.replace("'","")
	return string


def classificate(stream,x,y):
    
    # res è un dict che conterrà (per ogni parola da testare) tutte le classi
    # e ad ognuna corrisponderà la distanza minima trovata (con le parole che la 'compongono')
    res = {}
    # **************** PRIMA CLASSIFICAZIONE *****************
    # Per ogni classe calcolo la diumbstanza tra le parole di cui è composta e la parola da testare
    for classe in dictionary.keys():

        # For each term in the dictionary for each class i save the DL distance, then i pick the minimum per class
        dam = [(damerau_levenshtein_distance(stream, campo_misurato)) for campo_misurato in
            dictionary[classe]]  # array di distanze per classe

        if len(dam) > 0:
            res[classe] = min(dam) # I pick the minimum distance for each class

        #else:
            #res[classe] = 50 #Da modificare, ma per ora serve per evitare problemi con le classi senza parole
        distanza_minima = res[min(res, key=res.get)]
        classi_con_stessa_distanza_minima = []  # riempio una lista per vedere se la distanza minima trovata è duplicata
        for key, value in res.iteritems():  # TODO casi in cui ci sono distanze uguali !!
            if value == distanza_minima:
                # print 'distanza minima =', key
                classi_con_stessa_distanza_minima.append(key)

        if distanza_minima is 0:
        	# TODO non so se riclassificare -> può venir fuori lo stesso risultato
        	if len(classi_con_stessa_distanza_minima) > 1:  # è stata trovata più di una classe con distanza 0 -> riclassifico per quelle classi
        		#XXX res = riclassifica_per_tag(p, tags, classi_con_stessa_distanza_minima)
        		res = res #toglilo
        else:
        	"""
        	A questo punto, verifico due condizioni:
        	- se la distanza minima trovata tra tutte le classi è maggiore del x% di len(strea,)
        	- se ci sono due distanze molto simili che hanno differenza y% sulla lunghezza
        	"""
        	percent_lunghezza = (len(stream) * x) / 100
            #se non rispetta la condizione la assumo come buona
        	if distanza_minima > percent_lunghezza:
        		# riclassifico solo per alcune classi !?
        		# TODO cerco le classi con distanze simili alla distanza minima
        		# aggiungo alla lista di distanza minima simile, le classi con distanze diverse ma simili
        		for classe, dist in res.iteritems():
        			diff = (abs((distanza_minima - dist)) * y) / 100
        			if diff < percent_lunghezza and (dist != distanza_minima):
        				classi_con_stessa_distanza_minima.append(classe)
        				
        			#XXX res = riclassifica_per_tag(p, tags, classi_con_stessa_distanza_minima)

        # We decide finally the class and check whether is right or wrong
    
	
    classe_attribuita = min(res, key=res.get)
    return classe_attribuita

# We save all the stream IDs in a macro list, ready to be processed
# maxPages : number of pages to fetch in total
# threshold : number of pages after which start to parse along
def get_all_streams(maxPages, threshold):
	pageArray = [] # List of HTML pages (a pool)
	list_stream = [] # List of stream IDs
	
	# Start from the streams you already collected
	#list_stream += get_all_streams_local()

	# Fetch all the pages in the desired range
	# We get first HTML code and, once in a while, we parse them, empty the pool, and save the stream IDs
	counter = 0
	for i in range(0, maxPages):
		try:
			print "Getting page " + str(i) + "..."
			pageArray.append(urlopen("https://data.sparkfun.com/streams/?page=" + str(i)))
			
			# Start to parse from the pool (along one by one)
			if (i >= threshold) or (i >= maxPages - 1):
				html = pageArray.pop()
				list_stream += get_streams_from_html(html, list_stream)
		except:
			print (sys.exc_info()[0])
			continue
	# Empty the pool and parse the remainder
	for y in range(len(pageArray)):
		html = pageArray.pop()
		list_stream += get_streams_from_html(html, list_stream)
	print ("All in all we have " + str(len(list_stream)) + " streams to compute.")
	return list_stream

			
# Returns a list of stream URLs got from the HTML page
def get_streams_from_html(html, list_stream):
	list_stream_return = []
	for l in html.readlines():
		line = l.decode('utf-8').strip()  # All the lines tof the HTML document

		if "stream-title" in line:
			# Take the stream ID
			stream = line.split("\"")[3]
			if stream not in list_stream:
				list_stream_return.append(stream)

	return list_stream_return


def get_and_classificate(channels):
	list_valid_channels = []

	for channel in channels:
		print "Evaluating channel " + channel
		try:
			url = 'https://data.sparkfun.com' + channel + '.json'
			print "SI"
			response = requests.get(url)
			print "response"
			data_channel = json.loads(response.content)
			print data_channel	
			'''
			channel_doc = data_channel['stream']['_doc'] 
			
			if channel_doc["location"]:
				if channel_doc["location"]["country"].lower() == "italy" or channel_doc["location"]["country"].lower() == "italia" or channel_doc["location"]["country"].lower() == "it":
					print "In Italia"
					channel_id = trim_string(data_channel['publicKey']).decode('utf-8')

					channel_name = trim_string(channel_doc['title']).decode('utf-8')
					channel_description = trim_string(channel_doc['description']).decode('utf-8')

					dict = {'channel_id': channel_id,'name':channel_name,'description':channel_description,'latitude':channel_doc["location"]["lat"],'longitude':channel_doc["location"]["lng"]}
			'''	
			
		except UnicodeEncodeError:
			pass
		except KeyError:
			pass
		# What else?
		except:
			#print(sys.exc_info()[0])
			continue

	return list_valid_channels


if __name__ == "__main__":
	
	#urllib3.disable_warnings()
	requests.packages.urllib3.disable_warnings()
	maxP = int(sys.argv[1])
	thresh = int(sys.argv[2])
	
	myStreams = get_all_streams(maxP, thresh)

	channels = get_and_classificate(myStreams)
	

	