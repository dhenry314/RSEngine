from ..main import app, api
from ..configure import appConfig as config
from ..models.resources import Resources as res
from ..models.capabilities import Capabilities as caps
from ..api.ResourceSync import ResourceSync as rs

api.add_resource(res,
		 "/resource",
                 "/resource/<string:resID>",
                 methods=['GET','POST','DELETE'],
                 resource_class_kwargs={ 'config': config })

api.add_resource(caps,
				 "/capability",
                 "/capability/<string:capID>",
                 methods=['GET','POST','DELETE'],
                 resource_class_kwargs={ 'config': config })

api.add_resource(rs,
                 "/RS/<string:sourceNamespace>",
                 "/RS/<string:sourceNamespace>/<string:setNamespace>",
                 "/RS/<string:sourceNamespace>/<string:setNamespace>/<string:capability>",
                 methods=['GET'],
                 resource_class_kwargs={ 'config': config })
