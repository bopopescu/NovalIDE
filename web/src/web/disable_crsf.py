#coding:utf-8

class CsrfDisableMiddleware(object):
    def process_request(self, request): 
        request.csrf_processing_done = True
        ###setattr(request, '_dont_enforce_csrf_checks', True)
        return None
