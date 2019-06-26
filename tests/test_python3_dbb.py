import inspect

class _D:
    def _m(self): pass
    
class _C:
    def _m(self): pass
    
_x = _C()
_x2 = _D()

a=121111
r = input('hahah')
print(r)
raise AttributeError('Provider test already registered')

print (type(_C),_x.__class__,dir(_x),"------------")

import types
###print (dir(types))
print (type(inspect))
###print type(inspect) is types.InstanceType,"============="

print (type(_x),type(type))
print (inspect.isclass(_x))
print (inspect.isclass(_x2))
print (inspect.isclass(_D))
print (inspect.isclass(_C))
print (inspect.ismodule(_C))
print (isinstance(inspect,object),"------------")

print (1)
###print (g)
print (2)
print (3)
print (4)
print (6)
print (7)
print (8)
print (9)
print (10)
print ("11111111111111")