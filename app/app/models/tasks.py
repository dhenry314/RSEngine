import os
import json

import dramatiq
import requests
from zipfile import ZipFile
from dramatiq.brokers.redis import RedisBroker

from app.configure import appConfig

redis_broker = RedisBroker(host="redis", port=6379)
dramatiq.set_broker(redis_broker)

@dramatiq.actor()  
def createDump(batchPath,setPath,batchTag,sourceNamespace,setNamespace):
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
    capURI = str(appConfig.baseURI) + "/static/" + str(sourceNamespace) + "/" + str(setNamespace) + "/" + str(batchTag) + ".zip"
    return capURI
