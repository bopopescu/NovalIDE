# coding:utf-8

'''
WSGI middlewares.
'''
import re
import copy
import datetime

from bson import ObjectId, DBRef
from mongoengine import register_connection, Document, EmbeddedDocument
from django.conf import settings


class Init(object):
    _instance = None

    # singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Init, cls).__new__(cls)
            cls._instance._sealed = False
        return cls._instance

    def __init__(self, application=None, unittest=False, useTestDb=False, useTestCache=False, useTestGearman=False):
        if self._sealed:
            return
        self._sealed = True

        self.application = application

        # register mongodb connections.
        for k, v in settings.MONGODBS.items():
            # prepend 'test_' to db name when run unittest
            if unittest or useTestDb:
                v['name'] = 'test_'+v['name']
            conn_params = copy.deepcopy(v)
            name = conn_params.pop('name')
            register_connection(k, name, **conn_params)

        self._hook_docuement()

    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

    def _hook_docuement(self):
        #注入打印Document对象的方法Document.__unicode__ = lambda doc: ",".join([(x + "=" + str(doc._data[x])) for x in doc._data])
        def build_to_json(self, *args):
            out = dict(self._data)

            for k, v in out.items():
                #是否排除
                if args and (k not in args):
                    del out[k]
                    continue
                if k == "_id":
                    k = "id"

                if isinstance(v, ObjectId):
                    out[k] = str(v) if v else None
                elif isinstance(v, datetime.datetime):
                    out[k] = get_milliseconds_from_datetime(v)
                elif isinstance(v, DBRef):
                    out[k] = str(v.id) if v else None
                elif isinstance(v, (Document, EmbeddedDocument)):
                    out[k] = v.build_to_json(*args)

            return out

        #注入打包json的方法
        Document.build_to_json = build_to_json
