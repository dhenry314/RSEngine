# Common Utils
import requests
import json

from app.configure import appConfig

userAgent = appConfig.userAgent
hdrs = {
    'User-Agent': userAgent
}

def getContent(uri,tries=0):
     try:
         r = requests.get(uri,headers=hdrs)
     except requests.exceptions.HTTPError as e:
         raise ValueError("Could not get contents from " + str(uri) + " HTTPError: " + str(e))
     except requests.exceptions.RequestException as e:
         raise ValueError("Could not get contents from " + str(uri) + " RequestException: " + str(e))
     except requests.exceptions.TooManyRedirects:
         raise ValueError("Too many redirects for " + str(uri))
     except requests.exceptions.Timeout:
         if tries > 4:
             raise ValueError("Could not get content from " + str(uri))
         sleep(2)
         return Utils.getContent(uri,tries+1)
     if r.status_code != 200:
         raise ValueError("Could not get Content from "  + str(uri))
     contentType = r.headers['content-type']
     CTParts = contentType.split(";")
     mimeType = CTParts[0]
     MTParts = mimeType.split("/")
     ext = MTParts[1]
     if mimeType in ['text/html','text/plain','text/css','text/csv','application/json','application/javascript','application/xhtml+xml','application/xml']:
         return r.text, ext
     else:
         return r.content, ext

