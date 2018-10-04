import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, exc
 
Base = declarative_base()
 
class Resources(Base):
    __tablename__ = 'resources'
    ID = Column(Integer, nullable=False, primary_key=True)
    sourceNamespace = Column(String(256), nullable=False)
    setNamespace = Column(String(256), nullable=False)
    batchTag = Column(String(256))
    status = Column(String(20), default='created')
    lastmod = Column(DateTime, default=datetime.datetime.utcnow)
    URI = Column(String(767), nullable=False)
    hashVal = Column(String(256), nullable=False)
    
class Capabilities(Base):
    __tablename__ = 'capabilities'
    ID = Column(Integer, nullable=False, primary_key=True)
    URI = Column(String(256), nullable=False)
    sourceNamespace = Column(String(256), nullable=False)
    setNamespace = Column(String(256), nullable=False)
    capabilityType = Column(String(20), nullable=False)
    capParams = Column(String(767), nullable=True)
    
    
def commitItem(session,myItem):
    delay = 2
    tries = 0
    errMsg = None
    while tries < 4:
        try:
            session.add(myItem)
            session.commit()
        except exc.SQLAlchemyError as e:
            session.rollback()
            errMsg = str(e)
            delay *= 2
            tries += 1
        else:
            break
    if tries == 4:
        raise ValueError("Could not add item: " + str(myItem.URI) + " ERROR: " + str(errMsg))
        return False
    session.flush()
    return myItem.ID
        
def deleteItem(session,myItem):
    delay = 2
    tries = 0
    errMsg = None
    while tries < 4:
        try:
            session.delete(myItem)
            session.commit()
        except exc.SQLAlchemyError as e:
            session.rollback()
            errMsg = str(e)
            sleep(delay)
            delay *= 2
            tries += 1
        else:
            break
    if tries == 4:
        raise ValueError("Could not delete item: " + str(myItem.URI) + " ERROR: " + str(errMsg))
        return False
    session.flush()
    return True
   
 
