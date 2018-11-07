# RSEngine = a ResourceSync service

See http://www.openarchives.org/rs/1.1/resourcesync

On DockerHub: https://hub.docker.com/r/climatewalker/rsengine/

# Getting Started

1. Run docker-compose up -d
2. Post to http://localhost:81/resource with the parameters sourceNamespace, setNamespace, batchTag, and uri
  -- for example:
  ```
   %>curl -d "sourceNamespace=dhenry&setNamespace=climatewalker&batchTag=20181106&uri=http://climate-walker.org/the-book" -X POST http://localhost:81/resource
   ```
3. After posting resources to a given sourceNamespace, setNamespace and batchTag, you can create a dumpfile by posting to capability. 
  -- for example:
  ```
   %>curl -d "sourceNamespace=dhenry&setNamespace=climatewalker&batchTag=20181106" -X POST http://localhost:81/capability
   ```
   which returns the uri to the dump file: http://localhost:81/RS/dhenry/climatewalker/20181106.zip 
   -- then add the capability URI with:
   ```
   %>curl -d "sourceNamespace=dhenry&setNamespace=climatewalker&uri=http://localhost:81/RS/dhenry/climatewalker/20181106.zip&capabilityType=dump" -X POST http://localhost:81/capability
   ```
4.  You can then retrieve resources using the ResourceSync protocol:
   -- for example:
    http://localhost:81/RS/dhenry/climatewalker/resourcelistindex.xml might return:
     ```xml
     <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/" >
        <rs:ln
            rel="up"
            href="http://localhost:81/RS/dhenry/climatewalker/capabilitylist.xml"
        ></rs:ln>
        <rs:md 
            capability="resourcelist"
            at="2018-11-06T17:41:16.901455"
            completed="2018-11-06T17:41:16.901497"
         ></rs:md>
     <sitemap>
        <loc>http://localhost:81/RS/dhenry/climatewalker/resourcelist_0-4.xml</loc>
              <rs:md
                   at="2018-11-06T17:41:16.901471"
              ></rs:md>
             <rs:ln
                 rel="alternate"
                 href="http://localhost:32784/RS/dhenry/climatewalker/resourcelist_0-4.json"
                 type="application/json"
             ></rs:ln>
     </sitemap>
    </sitemapindex>
5. Opening http://localhost:81/RS/dhenry/climatewalker/resourcelist_0-4.xml, might return:
    ```xml
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/" >
        <rs:md capability="resourcelist"></rs:md>
         <url>
        <loc>http://climate-walker.org/</loc>
        
            <lastmod>2018-11-06T12:13:50</lastmod>
        
        
               <rs:ln 
               
                   href="/resource/1"
               
               
                   hash="describedby"
               
               ></rs:ln>
        
        
               <rs:md 
               
               
                   hash="md5:436e47e59d2afcba7aa5d8d9be2a21c3"
               
               ></rs:md>
               
        
    </url>
    
    <url>
        <loc>http://climate-walker.org/the-walk</loc>
        
            <lastmod>2018-11-06T12:14:24</lastmod>
        
        
               <rs:ln 
               
                   href="/resource/2"
               
               
                   hash="describedby"
               
               ></rs:ln>
        
        
               <rs:md 
               
               
                   hash="md5:22b9edb71edd611223554e065d193649"
               
               ></rs:md>
               
        
    </url>
        ...
6. Opening http://localhost:81/RS/dhenry/climatewalker/capabilitylist.xml shoud return:
      ```xml
      <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/" >
         <rs:md capability="capabilitylist"></rs:md>
      <url>
        <loc>http://localhost:81/static/dhenry/climatewalker/20181106.zip</loc>
      </url>
      <url>
        <loc>http://localhost:81/RS/dhenry/climatewalker/resourcelistindex.xml</loc>
      </url>
      <url>
        <loc>http://localhost:81/RS/dhenry/climatewalker/changelistindex.xml</loc>
      </url>
    </urlset>

