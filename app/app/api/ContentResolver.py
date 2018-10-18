import os
import numpy as np
import magic
from flask import make_response, jsonify, render_template
from flask_restful import Resource, abort, marshal, fields

from ..models import resources as res

class ContentResolver(Resource):

    resourceMgr = None

    def __init__(self,**kwargs):
        self.config = kwargs['config']
        self.staticFiles = self.config.staticFiles
        self.resourceMgr = res.Resources(config=self.config)
                
    def get(self,resID):
        resource = None
        resource = self.resourceMgr.getByID(resID)
        if not resource:
            abort(404, message="No such resourceID: " + str(resID))
        batchPath = str(self.staticFiles) + str(resource.sourceNamespace) + "/" + str(resource.setNamespace) + "/" + str(resource.batchTag)
        IDName = np.base_repr(resource.ID, 36)
        IDPath = IDName.zfill(4)
        relativeDir = "/" + str(IDPath[0]) + "/" + str(IDPath[1]) + "/" + str(IDPath[2]) + "/" + str(IDPath[3])
        path = batchPath + relativeDir
        files = os.listdir(path)
        content = None
        fullPath = None
        for fileName in files:
            parts = fileName.split('.')
            if str(parts[0]) == IDName:
                fullPath = str(path) + "/" + str(fileName)
                f=open(fullPath , "r")
                content = f.read()
        if not fullPath:
            abort(404, message="No path found for resourceID: " + str(resID))
        if not content:
            abort(404, message="No content found for resourceID: " + str(resID))
        resp = make_response(content, 200)
        resp.mimetype = magic.from_file(fullPath)
        return resp 
