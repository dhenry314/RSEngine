import os
import json
import shutil

import dramatiq
import requests
from zipfile import ZipFile
from dramatiq.brokers.redis import RedisBroker

from app.configure import appConfig

if 'REDIS_HOST' in os.environ:
    redis_broker = RedisBroker(url=os.environ['REDIS_HOST'])
else:
    redis_broker = RedisBroker(host="redis", port=6379)
dramatiq.set_broker(redis_broker)

@dramatiq.actor()  
def createDump(batchPath,setPath,batchTag,sourceNamespace,setNamespace,baseURI):
    file_paths = []
    for root, directories, files in os.walk(batchPath): 
        for filename in files: 
            # join the two strings in order to form the full filepath. 
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    zipPath = str(setPath) + "/" + str(batchTag) + ".zip"
    with ZipFile(zipPath,'w') as zip: 
        for file in file_paths:
            arcPath = file.replace(setPath,'')
            zip.write(file,arcPath)
    capURI = str(baseURI) + "/static/" + str(sourceNamespace) + "/" + str(setNamespace) + "/" + str(batchTag) + ".zip"
    return capURI
    
@dramatiq.actor()  
def removeDump(dumpURI,baseURI,staticFiles):
    staticBase = str(baseURI) + '/static/'
    if dumpURI.startswith(staticBase):
        subPath = dumpURI.replace(staticBase,'')
        zipPath = str(staticFiles) + str(subPath)
        if os.path.isfile(zipPath):
            os.remove(zipPath)
        if '.zip' in zipPath:
            batchPath = zipPath.replace('.zip','')
            if os.path.isdir(batchPath):
                #find manifest
                manifestPath = str(batchPath) + '/manifest'
                if os.path.isfile(manifestPath):
                    with open(manifestPath) as infile:
                        for line in infile:
                            parts = line.split("><")
                            contentPath = str(batchPath) + str(parts[1])
                            os.remove(contentPath)
                            resourcePath = parts[3]
                            resourcePath = resourcePath.replace(">","")
                            resourceURI = str(baseURI) + str(resourcePath)
                            requests.delete(resourceURI)
                    os.remove(manifestPath)
                shutil.rmtree(batchPath)
                
