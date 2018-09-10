import sys
from app.models import model
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, exc
from flask_restful import Api, Resource, reqparse, abort, marshal, fields #yum! Frango mints!

parser = reqparse.RequestParser()
parser.add_argument('uri')
parser.add_argument('sourceNamespace')
parser.add_argument('setNamespace')
parser.add_argument('capabilityType')
parser.add_argument('offset',type=int)
parser.add_argument('count',type=int)

capability_fields = {
    "ID": fields.Integer,
    "sourceNamespace": fields.String,
    "setNamespace": fields.String,
    "URI": fields.String,
    "capabilityType": fields.String
}

class Capabilities(Resource):

    def __init__(self,**kwargs):
        self.config = kwargs['config']
        self.defaultResourceUnit = self.config.defaultResourceUnit
        self.baseURI = self.config.baseURI
        model.engine = create_engine(self.config.db['uri'])
        model.Base.metadata.create_all(model.engine)
        Session = sessionmaker(bind=model.engine)
        self.session = Session()

    def get(self,capID=None):
        if capID:
            capability = self.getByID(capID)
            return self.handleCapability(capability)
        args = parser.parse_args()
        offset = None
        count = None
        if 'offset' in args:
            offset = args['offset']
        if 'count' in args:
            count = args['count']
        capabilities = self.getAll(offset,count)
        if not capabilities:
            abort(404, message="Capability {} doesn't exist")
        results = []
        for capability in capabilities:
            thisCap = marshal(capability,capability_fields)
            results.append(thisCap)
        return results,200
        
    def post(self):
        args = parser.parse_args()
        capability = self.add( args['uri'], args['sourceNamespace'], args['setNamespace'], args['capabilityType'])
        return self.handleCapability(capability)
        
    def delete(self,capID=None):
        capability = None
        if capID:
            capability = self.getByID(capID)
        if not capability:
            abort(404, message="Capability {} doesn't exist")
        result = model.deleteItem(self.session,capability)
        if not result:
            abort(500, message="Capability could not be deleted!")
        return {"msg": "capability " + str(capability.URI) + " has been deleted."}
        
    def handleCapability(self,capability):
        if not capability:
            abort(404, message="Capability {} doesn't exist")
        return marshal(capability, capability_fields), 200

    def getAll(self,offset=0,count=100):
        if not offset:
            offset = 0
        if not count:
            count = self.defaultResourceUnit
        result = self.session.query(model.Capabilities).offset(offset).limit(count).all()
        if not result:
           return False
        return result

    def getByID(self,capID):
        result = self.session.query(model.Capabilities).filter(
            model.Capabilities.ID == capID
        ).first()
        if not result:
            return False
        return result
        
    def getByURI(self,uri):
        result = self.session.query(model.Capabilities).filter(
            model.Capabilities.URI == uri
        ).first()
        if not result:
           return False
        return result
        
    def add(self,uri,source_namespace,set_namespace,capabilityType):
        existingCap = self.getByURI(uri)
        if existingCap:
            abort(404, message="Capability {} already exists")
        myCap = model.Capabilities()
        capProps = {
                'sourceNamespace':source_namespace,
                'setNamespace':set_namespace,
                'URI':uri,
                'capabilityType': capabilityType
        }
        for key, value in capProps.items():
            setattr(myCap, key, value)
        capID = model.commitItem(self.session,myCap)
        myCap.ID = capID
        return myCap
