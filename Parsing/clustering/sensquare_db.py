#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
__author__ = 'Davide'


import MySQLdb
import sys
import datetime

class MyDB(object):
    _db_connection = None
    _db_cur = None

    def __init__(self):
        self._db_connection = MySQLdb.connect("localhost","davidek","tesiCRESTINI2016","sensquare")
        self._db_cur = self._db_connection.cursor()

    def store_channel_and_streams(self,channel,streams):
        print "Storing on DB"    
        db = MySQLdb.connect("localhost","davidek","tesiCRESTINI2016","sensquare")
        #Prima creo il device poi i datastreams, poi le misurazioni relaive ad ogni datastream
        cur = db.cursor()
        query_device = 'INSERT INTO Devices (ID,name,device_type,participant_id)\
        VALUES("{}","{}","STEADY",5)'.format(channel['name'],channel['name'])
        cur.execute(query_device)
        for stream in streams:
            query_stream = 'INSERT INTO DataStreams (name,data_class,description,url,last_entry_ID,device_id,reliability)\
            VALUES("{}","{}","{}","{}",-1,"{}",50)'.format(stream['stream_name'],stream['stream_class'],channel['description'],channel['url'],channel['name'])
            cur.execute(query_stream)
            data = cur.fetchall()            
            stream_id = cur.lastrowid
            i = 0
            for measure in stream['measurements']:
                if i < 5:
                    query_measure = 'INSERT INTO Measurements (data_stream_ID,GPS_latitude,GPS_longitude,MGRS_coordinates,value,timestamp)\
                    VALUES({},{},{},"-1",{},"{}")'.format(stream_id,channel['latitude'],channel['longitude'],measure['value'],measure['timestamp'])
                    print query_measure
                    cur.execute(query_measure)

                i = i +1
        db.commit()
        db.close()
        print "salvato"

    def __del__(self):
        self._db_connection.close()