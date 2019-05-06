from functools import wraps
class Singleton_PY2(type):  
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)  
        cls._instance = None  
    
    def __call__(cls, *args, **kw):  
        if cls._instance is None:  
            cls._instance = super(Singleton, cls).__call__(*args, **kw)  
        return cls._instance


def Singleton(cls):
    instances = {}
    
    @wraps(cls)
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return getinstance