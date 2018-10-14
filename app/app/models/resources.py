import sys
import os

import requests
import urllib3
import hashlib
import numpy as np
from datetime import date, datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask_restful import Api, Resource, reqparse, abort, marshal, fields

from app.models import model
import app.models.Utils as Utils

parser = reqparse.RequestParser()
parser.add_argument('uri')
parser.add_argument('sourceNamespace')
parser.add_argument('setNamespace')
parser.add_argument('batchTag')
parser.add_argument('offset',type=int)
parser.add_argument('count',type=int)

resource_fields = {
    "sourceNamespace": fields.String,
    "setNamespace": fields.String,
    "batchTag": fields.String,
    "ID": fields.Integer,
    "status": fields.String,
    "lastmod": fields.String,
    "URI": fields.String,
    "hashVal": fields.String
}

class Resources(Resource):

    def __init__(self,**kwargs):
        self.config = kwargs['config']
        self.defaultResourceUnit = self.config.defaultResourceUnit
        self.baseURI = self.config.baseURI
        self.hashAlgorithm = self.config.hashAlgorithm
        self.staticFiles = self.config.staticFiles
        model.engine = create_engine(self.config.db['uri'])
        model.Base.metadata.create_all(model.engine)
        Session = sessionmaker(bind=model.engine)
        self.session = Session()

    def get(self,resID=None):
        if resID:
            resource = self.getByID(resID)
            return self.handleResource(resource)
        args = parser.parse_args()
        offset = None
        count = None
        if 'offset' in args:
            offset = args['offset']
        if 'count' in args:
            count = args['count']
        resources = self.getAll(offset,count)
        if not resources:
            abort(404, message="Resource {} doesn't exist")
        results = []
        for resource in resources:
            thisRes = marshal(resource,resource_fields)
            results.append(thisRes)
        return results,200
        
    def post(self):
        batchTag = None
        args = parser.parse_args()
        if 'batchTag' in args:
            batchTag = args['batchTag']
        try:
            resource = self.add( args['uri'], args['sourceNamespace'], args['setNamespace'], batchTag)
        except ValueError as e:
            abort(404, message=str(e))
        return self.handleResource(resource)
        
    def delete(self,resID=None):
        resource = None
        if resID:
            resource = self.getByID(resID)
        if not resource:
            abort(404, message="Resource {} doesn't exist")
        result = model.deleteItem(self.session,resource)
        if not result:
            abort(500, message="Resource could not be deleted!")
        return {"msg": "resource " + str(resource.URI) + " has been deleted."}
        
    def handleResource(self,resource):
        if not resource:
            abort(404, message="Resource {} doesn't exist")
        return marshal(resource, resource_fields), 200

    def getAll(self,offset=0,count=100):
        if not offset:
            offset = 0
        if not count:
            count = self.defaultResourceUnit
        result = self.session.query(model.Resources).offset(offset).limit(count).all()
        if not result:
           return False
        return result

    def getByURI(self,uri):
        result = self.session.query(model.Resources).filter(
            model.Resources.URI == uri
        ).first()
        if not result:
           return False
        return result
        
    def getExisting(self,uri,sourceNamespace,setNamespace):
        result = self.session.query(model.Resources).filter(
            model.Resources.URI == uri,
            model.Resources.sourceNamespace == sourceNamespace,
            model.Resources.setNamespace == setNamespace
        ).first()
        if not result:
           return False
        return result
        
    def getByID(self,resID):
        result = self.session.query(model.Resources).filter(
            model.Resources.ID == resID
        ).first()
        if not result:
            return False
        return result
        
    def add(self,uri,sourceNamespace,setNamespace,batchTag=None):
        existingRes = self.getExisting(uri,sourceNamespace,setNamespace)
        if existingRes:
            return marshal(existingRes,resource_fields)
        Rstatus = "created"
        myResource = None
        try:
            uriContents, ext = Utils.getContent(uri)
        except ValueError as e:
            raise ValueError(str(e))
        contentHash = self.getHash(uriContents,self.hashAlgorithm)
        if existingRes:
            if contentHash == existingRes.hashVal:
                return existingRes
            else:
                myResource = existingRes
                Rstatus = "updated"
        else:
            myResource = model.Resources()
        resProps = {
                'sourceNamespace':sourceNamespace,
                'setNamespace':setNamespace,
                'batchTag': batchTag,
                'status':Rstatus,
                'URI':uri,
                'lastmod':datetime.today(), 
                'hashVal':contentHash
        }
        for key, value in resProps.items():
            setattr(myResource, key, value)
        resID = model.commitItem(self.session,myResource)
        myResource.ID = resID
        self.cacheResult(myResource,uriContents,ext)
        return marshal(myResource,resource_fields)

    def cacheResult(self,resource,contents,ext):
        #set initial path
        batchPath = str(self.staticFiles) + "/" + str(resource.sourceNamespace) + "/" + str(resource.setNamespace) + "/" + str(resource.batchTag)
        IDName = np.base_repr(resource.ID, 36)
        IDPath = IDName.zfill(4)
        relativeDir = "/" + str(IDPath[0]) + "/" + str(IDPath[1]) + "/" + str(IDPath[2]) + "/" + str(IDPath[3])
        path = batchPath + relativeDir
        if not os.path.isdir(path):
            os.makedirs( path )
        relativePath = str(relativeDir) + "/" + str(IDName) + "." + str(ext)
        manifestLine = "<" + str(resource.URI) + "><" + str(relativePath) + "><" + str(resource.hashVal) + "></resource/" + str(resource.ID) + ">\n"
        fullPath = str(path) + "/" + str(IDName) + "." + str(ext)
        f = open(fullPath, "w")
        try:
            f.write(contents)
        except TypeError:
            f.write(contents.decode("UTF-8")) 
        f.close()
        manifestPath = str(batchPath) + "/manifest"
        if not os.path.isfile(manifestPath):
            f1 = open(manifestPath,"w")
        else: 
            f1 = open(manifestPath, "a")
        f1.write(manifestLine)
        f1.close()
       
    def getHash(self,hashable,ha):
        try:
            hashable = hashable.encode('utf-8')
        except AttributeError as e:
            pass
        if ha == "md5":
            m = hashlib.md5()
        elif ha == "sha1":
            m = hashlib.sha1()
        elif ha == "sha224":
            m = hashlib.sha224()
        elif ha == "sha256":
            m = hashlib.sha256()
        elif ha == "sha384":
            m = hashlib.sha384()
        elif ha == "sha512":
            m = hashlib.sha512()
        else:
            return False
        m.update(hashable)
        return str(ha) + ":" + str(m.hexdigest())

    
    
