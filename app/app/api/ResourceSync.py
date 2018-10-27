import sys
from ..models import model
import json
from datetime import date, datetime, timedelta
from flask import make_response, jsonify, render_template
from flask_restful import Resource, abort
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from math import ceil
import dateutil.parser as dp

class ResourceSync(Resource):

    def __init__(self,**kwargs):
        self.config = kwargs['config']
        self.baseURI = self.config.baseURI
        model.engine = create_engine(self.config.db['uri'])
        model.Base.metadata.create_all(model.engine)
        Session = sessionmaker(bind=model.engine)
        self.session = Session()
        self.extension = None
        self.defaultResourceUnit = int(self.config.defaultResourceUnit)
        self.defaultDateUnit = self.config.defaultDateUnit
        self.resCnt = 0
        
    def parseFileName(self,filename):
        extension = None
        if '.' in filename:
            parts = filename.split('.')
            extension = parts.pop()
            filename = '.'.join(parts)
        return filename,extension
    
    def getResourceCount(self,sourceNamespace,setNamespace=None):
        resCnt = self.session.query(model.Resources)
        if setNamespace:
            resCnt = self.session.query(model.Resources).filter(
                model.Resources.sourceNamespace == sourceNamespace,
                model.Resources.setNamespace == setNamespace
            ).count()
            return resCnt
        else:
            resCnt = self.session.query(model.Resources).filter(
                model.Resources.sourceNamespace == sourceNamespace
            ).count()
            return resCnt
        return 0
        
    def get(self,sourceNamespace,setNamespace=None,capability=None):
        self.resCnt = self.getResourceCount(sourceNamespace,setNamespace)
        if self.resCnt == 0:
            abort(404, message="No resources found for the given namespaces.")
        if not setNamespace:
            return self.getSourceDescription(sourceNamespace)
        if not capability:
            setFileName, setExt = self.parseFileName(setNamespace)
            if setFileName.lower() == 'description': 
                if setExt:
                    self.extension = setExt
                return self.getSourceDescription(sourceNamespace)
            return self.getCapabilityList(sourceNamespace,setNamespace)
        capLower = capability.lower()
        capLower = capLower.strip()
        capLower, capExt = self.parseFileName(capLower)
        if capExt:
            self.extension = capExt
        if capLower == 'capabilitylist':
            return self.getCapabilityList(sourceNamespace,setNamespace)
        if 'resourcelistindex' in capLower:
            return self.getResourceListIndex(capLower,sourceNamespace,setNamespace)
        if 'resourcelist' in capLower:
            return self.getResourceList(capLower,sourceNamespace,setNamespace)
        if 'changelistindex' in capLower:
            return self.getChangeListIndex(capLower,sourceNamespace,setNamespace)
        if 'changelist' in capLower:
            return self.getChangeList(capLower,sourceNamespace,setNamespace)
        
        abort(404, message="Capability {} doesn't exist".format(capability))
        return False

    def handleResponse(self,data,code):
        if self.extension == 'xml':
            if 'sitemapindex' in data:
                result_xml = render_template('sitemapindex.xml', md=data['sitemapindex']['rs:md'], ln=data['sitemapindex']['rs:ln'], sitemaps=data['sitemapindex']['sitemap'])
            else :
                result_xml = render_template('urlset.xml', md=data['urlset']['rs:md'], urlset=data['urlset']['url'])
            response = make_response(result_xml,code)
            response.headers['content-type'] = 'application/xml'
        else:
            response = make_response(jsonify(data),code)
            response.headers['content-type'] = 'application/json'
        return response

    def initURLSet(self,capabilityType):
        return {
				"urlset": {
					"@context": { "rs": "http://www.openarchives.org/rs/terms/" },
					"rs:md": {"@capability":capabilityType}
				}
		}
		
    def initSitemapIndex(self,capabilityType,sourceNamespace,setNamespace):
        upURI = str(self.baseURI) + '/RS/' + str(sourceNamespace) + '/' + str(setNamespace) + '/capabilitylist.xml'
        return {
				"sitemapindex": {
					"@context": { "rs": "http://www.openarchives.org/rs/terms/" },
					"rs:md": {"@capability":capabilityType },
					"rs:ln": { "@rel":"up", "@href": upURI}
				}
		}

    def getSourceDescription(self,sourceNamespace):
        #get distinct sets
        sourceDesc = self.initURLSet("description")
        setResults = self.session.query(model.Resources.setNamespace.distinct()).filter(
            model.Resources.sourceNamespace == sourceNamespace
        ).all()
        urls = []
        for setResult in setResults:
            url = { "rs:md": {"@capability":"capabilityList"}}
            setName = setResult[0]
            url['loc'] = str(self.baseURI) + "/RS/" + str(sourceNamespace) + "/" + str(setName)
            urls.append(url)
        sourceDesc['urlset']['url'] = urls
        return self.handleResponse(sourceDesc,200)

    def getCapabilityList(self,sourceNamespace,setNamespace):

        #get saved capabilities
        results = self.session.query(model.Capabilities).filter(
            model.Capabilities.sourceNamespace == sourceNamespace,
            model.Capabilities.setNamespace == setNamespace
        ).all()
        capabilities = []
        for result in results:
            capability = self.getCapabilityDict(result)
            capabilities.append(capability)
        #add default capabilities
        setURI = upURI = str(self.baseURI) + '/RS/' + str(sourceNamespace) + '/' + str(setNamespace) 
        capabilities.append({'loc': str(setURI) + '/resourcelistindex.xml'})
        capabilities.append({'loc': str(setURI) + '/changelistindex.xml'})
        capList = self.initURLSet("capabilitylist")
        capList['urlset']['url'] = capabilities
        return self.handleResponse(capList,200)
        
    def getResourceList(self,capLower,sourceNamespace,setNamespace):
        offset = 0
        count = 1000
        resourceList = self.initURLSet("resourcelist")
        resources = []
        capLower, capExt = self.parseFileName(capLower)
        if capExt:
            self.extension = capExt
        if '_' in capLower:
            parts = capLower.split('_')
            rawParams = parts.pop()
            params = rawParams.split('-')
            if len(params) != 2:
                abort(404, message="Capability {} doesn't exist".format(capLower))
            offset = int(params[0])
            endPos = int(params[1])
            count = endPos - offset
            if count < 1:
                abort(404, message="Capability {} doesn't exist".format(capLower))
        results = self.session.query(model.Resources).filter(
            model.Resources.sourceNamespace == sourceNamespace,
            model.Resources.setNamespace == setNamespace
        ).offset(offset).limit(count).all()
        
        for result in results:
             resourceDict = self.getResourceDict(result)
             resources.append(resourceDict)
        resourceList['urlset']['url'] = resources
        return self.handleResponse(resourceList,200)
        
    def getResourceListIndex(self,capLower,sourceNamespace,setNamespace):
        resourceListIndex = self.initSitemapIndex("resourcelist",sourceNamespace,setNamespace)
        resourceListIndex['sitemapindex']['rs:md']["@at"] = datetime.now().isoformat()
        totalRecordCnt = self.resCnt
        currentResCnt = self.resCnt
        sitemaps = []
        startNum = 0
        endNum = 999
        if endNum > totalRecordCnt:
                endNum = totalRecordCnt
        while currentResCnt > 0:
            urlBase = str(self.baseURI) + "/RS/" + str(sourceNamespace) + "/" + str(setNamespace) + "/resourcelist_" + str(startNum) + "-" + str(endNum)
            sitemap = { "rs:md": {"@at":datetime.now().isoformat()}}
            sitemap['loc'] = urlBase + ".xml"
            sitemap["rs:ln"] = { "@rel":"alternate", "@href": urlBase + ".json","@type": "application/json"}
            sitemaps.append(sitemap)
            startNum = startNum + 1000
            endNum = endNum + 1000
            if endNum > totalRecordCnt:
                endNum = totalRecordCnt
            currentResCnt = currentResCnt - 1000
        resourceListIndex['sitemapindex']['sitemap'] = sitemaps
        resourceListIndex['sitemapindex']['rs:md']['@completed'] = datetime.now().isoformat()
        return self.handleResponse(resourceListIndex,200)
        
        
    def parseDates(self,rawDate=None):
        dateInfo = {}
        dateLevel = "day"
        dateLevelOffset = 7 
        queryDateOffset = 10
        uriDate1 = None
        now = datetime.now()
        day = 1
        month = now.month
        year = now.year
        hour = 0
        minute = 0
        date1 = None
        date2 = None
        isoDate1 = None
        isoDate2 = None
        if not rawDate:
            rawDate = 'NA'
            day = now.day
            month = now.month
            year = now.year
            hour = now.hour
        if '-' in rawDate:
            # mysql datestamp in {year}-{month}-{day} {hour}:{minute}:{second} format (not quite ISO)
            if not 'T' in rawDate:
                isoTmp1 = rawDate.replace(' ','T')
            else: 
                isoTmp1 = rawDate
            date1 = dp.parse(isoTmp1)
            if len(rawDate) == 7:
                dateLevel = "month"
            if len(rawDate) == 13:
                dateLevel = "hour"
            if len(rawDate) == 16:
                dateLevel = "minute"
        else:
            # simple datetimestamp in {year}{month}{day}{hour}{minute} format
            if len(rawDate) >= 6:
                year = int(rawDate[0:4])
                month = int(rawDate[4:6])
                dateLevel = "month"
                if len(rawDate) >= 8:
                    day = int(rawDate[6:8])
                    dateLevel = "day"
                    if len(rawDate) >= 10:
                        hour = int(rawDate[8:10])
                        dateLevel = "hour"
                        if len(rawDate) >= 12:
                            minute = int(rawDate[10:12])
                            dateLevel = "minute"
                            if len(rawDate) > 12:
                                return False
        if not year:
            return False
        if not month:
            return False
        if not date1:
            date1 = datetime(year=year,month=month,day=day,hour=hour,minute=minute)
        isoDate1 = date1.isoformat()
        year = date1.year
        month = date1.month
        day = date1.day
        hour = date1.hour
        minute = date1.minute
        if dateLevel == "month":
            dateLevelOffset = 4
            queryDateOffset = 7
            day2 = 1
            year2 = date1.year
            month2 = date1.month + 1
            if month2 == 12:
                year2 = year2 + 1
            date2 = datetime(year2,month2,day2)
            isoDate2 = date2.isoformat()
        else:
            if dateLevel == "day":
                dateLevelOffset = 7 
                queryDateOffset = 10
                diff1 = timedelta(days=1)
            if dateLevel == "hour":
                dateLevelOffset = 10
                queryDateOffset = 13
                diff1 = timedelta(hours=1)
            if dateLevel == "minute":
                dateLevelOffset = 13
                queryDateOffset = 16
                diff1 = timedelta(minutes=1)
            date2 = date1 + diff1
            isoDate2 = date2.isoformat()
        uriDate2 = str(year) + "{:02}".format(month)
        uriDate1 = uriDate2
        if queryDateOffset >= 10:
            uriDate2 = uriDate2 + "{:02}".format(day)
            if queryDateOffset >= 13:
                uriDate1 = uriDate1 + "{:02}".format(day)
                uriDate2 = uriDate2 + "{:02}".format(hour)
                if queryDateOffset >= 16:
                    uriDate1 = uriDate1 + "{:02}".format(hour)
                    uriDate2 = uriDate2 + "{:02}".format(minute)
                    if queryDateOffset >= 19:
                        uriDate1 = uriDate1 + "{:02}".format(minute)
        dateInfo = {'year':year,'month':month,'day':day,'hour':hour,'minute':minute,
		'isoDate1':isoDate1,'isoDate2':isoDate2, 'dateLevel':dateLevel, 
		'dateLevelOffset': dateLevelOffset,
		'queryDateOffset':queryDateOffset,'uriDate1':uriDate1,'uriDate2':uriDate2}
        return dateInfo
        
    def getChangeList(self,capLower,sourceNamespace,setNamespace):
        changeList = self.initURLSet("changelist")
        resources = []
        capLower, capExt = self.parseFileName(capLower)
        if capExt:
            self.extension = capExt
        capOnly = None
        rawDate = None
        pageRaw = None
        page = None
        offset = 0
        limit = self.defaultResourceUnit
        if '_' in capLower:
            parts = capLower.split('_')
            #may include a page number
            if len(parts) > 2:
                pageRaw = parts.pop()
                page = int(pageRaw)-1
                if page < 0:
                    abort(404, message="Capability {} doesn't exist".format(capLower))
            if len(parts) != 2:
                abort(404, message="Capability {} doesn't exist".format(capLower))
            rawDate = parts.pop()
            capOnly = parts.pop()
            if len(rawDate) < 6:
                abort(404, message="Capability {} doesn't exist".format(capLower))
            dateInfo = self.parseDates(rawDate)
        else:
            dateInfo = self.parseDates()
        if not dateInfo:
                abort(404, message="Capability {} doesn't exist".format(capLower))
        date1 = dp.parse(dateInfo['isoDate1'])
        date2 = dp.parse(dateInfo['isoDate2'])

        if not pageRaw:
            resCnt = self.session.query(model.Resources).filter(
                model.Resources.sourceNamespace == sourceNamespace,
                model.Resources.setNamespace == setNamespace,
                model.Resources.lastmod >= date1,
                model.Resources.lastmod <= date2
            ).count()
            if resCnt > self.defaultResourceUnit:
                if capOnly:
                    capLower = capOnly
                return self.getChangeListSubIndex(capLower,sourceNamespace,setNamespace,dateInfo)
        else:
            #define offset page number
            offset = page*self.defaultResourceUnit
        results = self.session.query(model.Resources).filter(
            model.Resources.sourceNamespace == sourceNamespace,
            model.Resources.setNamespace == setNamespace,
            model.Resources.lastmod >= date1,
            model.Resources.lastmod <= date2
        ).offset(offset).limit(limit).all()
        resultCount = 0;
        for result in results:
             resourceDict = self.getResourceDict(result)
             resources.append(resourceDict)
             resultCount = resultCount + 1
        changeList['urlset']['url'] = resources
        changeList['urlset']['rs:md']['@from'] = dateInfo['isoDate1']
        changeList['urlset']['rs:md']['@until'] = dateInfo['isoDate2']
        changeList['urlset']['resultCount'] = resultCount
        return self.handleResponse(changeList,200)

    def getChangeListSubIndex(self,capLower,sourceNamespace,setNamespace,dateInfo):
        baseURL = str(self.baseURI) + "/RS/" + str(sourceNamespace)
        baseURL = baseURL + "/" + str(setNamespace) + "/" + str(capLower) + "_"
        changeListIndex = self.initSitemapIndex("changelist",sourceNamespace,setNamespace)
        queryStr = "SELECT count(*) as recCount, substr(lastmod,1," + str(dateInfo['queryDateOffset']) +") as subDate FROM `resources` "
        queryStr = queryStr + " WHERE lastmod > '" + str(dateInfo['isoDate1']) + "' "
        queryStr = queryStr + " AND lastmod < '" + str(dateInfo['isoDate2']) + "' GROUP BY subDate"
        sql = text( queryStr )
        dateResults = model.engine.execute(sql)
        sitemaps = []
        for dateResult in dateResults:
            nextDateInfo = self.parseDates(dateResult.subDate)
            nextURL = {
						"loc": baseURL + str(nextDateInfo['uriDate1'] + ".xml"), 
						"rs:md": { "@from": nextDateInfo['isoDate1'], "@until": nextDateInfo['isoDate2']}, 
						"rs:ln": { "@rel":"alternate", "@href": baseURL + str(nextDateInfo['uriDate1']) + ".json", "@type": "application/json"}
					  }
            sitemaps.append(nextURL)
        changeListIndex['sitemapindex']['sitemap'] = sitemaps
        changeListIndex['sitemapindex']['rs:md']['@from'] = dateInfo['isoDate1']
        changeListIndex['sitemapindex']['rs:md']['@until'] = dateInfo['isoDate2']
        return self.handleResponse(changeListIndex,200)
         
    def getChangeListIndex(self,capLower,sourceNamespace,setNamespace):
        dateInfo = self.parseDates()
        baseURL = str(self.baseURI) + "/RS/" + str(sourceNamespace) + "/" + str(setNamespace) + "/changelist_"
        changeListIndex = self.initSitemapIndex("changelist",sourceNamespace,setNamespace)
        queryStr = "SELECT count(*) as recCount, "
        queryStr = queryStr + " substr(lastmod,1," + str(dateInfo['dateLevelOffset']) + ") "
        queryStr = queryStr + " as subDate FROM `resources` "
        queryStr = queryStr + " WHERE sourceNamespace = '" + str(sourceNamespace)
        queryStr = queryStr + "' AND setNamespace = '" + str(setNamespace) + "' "
        queryStr = queryStr +  " GROUP BY subDate"
        sql = text( queryStr )
        dateResults = model.engine.execute(sql)
        sitemaps = []
        for dateResult in dateResults:
            nextDateInfo = self.parseDates(dateResult.subDate)
            nextURL = {
              "loc": baseURL + str(nextDateInfo['uriDate1'] + ".xml"), 
              "rs:md": { "@from": nextDateInfo['isoDate1'], "@until": nextDateInfo['isoDate2']}, 
              "rs:ln": { "@rel":"alternate", "@href": baseURL + str(nextDateInfo['uriDate1']) + ".json", "@type": "application/json"}
            }
            sitemaps.append(nextURL)
        changeListIndex['sitemapindex']['sitemap'] = sitemaps
        changeListIndex['sitemapindex']['rs:md']['@from'] = dateInfo['isoDate1']
        changeListIndex['sitemapindex']['rs:md']['@until'] = dateInfo['isoDate2']
        return self.handleResponse(changeListIndex,200)
        
    def getResourceDict(self,record):
        resource = {}
        resource['loc'] = record.URI
        #extract lastmod
        lastmod = None
        if isinstance(record.lastmod, (datetime, date)):
            lastmod = record.lastmod.isoformat()
        resource['lastmod'] = '{0:%Y-%m-%dT%H:%M:%S}'.format(record.lastmod)
        resource['rs:md'] = {"hash": record.hashVal}
        resourceURL = "/resource/" + str(record.ID)
        resource['rs:ln'] = {"rel":"describedby","href":resourceURL}
        return resource
        
    def getCapabilityDict(self,record):
        capability = {}
        capability['loc'] = record.URI
        return capability
