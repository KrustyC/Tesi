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
        
        self._db_cur = self._db_connection.cursor()

    def get_training_set_relevant_streams(self):
        query = u'Select Field.Id,Field.Field_name,Field.Class,Channel.Description,Channel.Name,Channel.Id\
                  From Field Inner Join Channel on Field.Channel_id = Channel.Id\
                  Where Class In ("Temperature","Dust_Level","Gas_Level","Brightness","Power","UV","Heat_Index","Pressure",\
                  "Rain_Index", "Radiation", "Humidity", "Wind_Direction", "Wind_Speed") '

        response = self._db_cur.execute(query)
        self._db_connection.commit()
        data = self._db_cur.fetchall()
        dict = []
        for item in data:
            dict.append({'field_id': item[0],'field_name':item[1],'field_class':item[2],'channel_description':item[3],'channel_name':item[4],'channel_id':item[5]})

        return dict

    def __del__(self):
        self._db_connection.close()