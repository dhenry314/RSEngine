import os

class appConfig:
    db = dict(
        uri = os.environ['DB_URI']
    )
    hashAlgorithm = os.environ['HASH_ALGORITHM']
    defaultResourceUnit = os.environ['RESOURCE_UNIT']
    defaultDateUnit = os.environ['DATE_UNIT']
    staticFiles = os.environ['STATIC_FILES']
    userAgent = os.environ['USER_AGENT']
