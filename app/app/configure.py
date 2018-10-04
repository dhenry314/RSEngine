import os

class appConfig:
    db = dict(
        uri = os.environ['DB_URI']
    )
    hashAlgorithm = os.environ['HASH_ALGORITHM']
    baseURI = os.environ['BASE_URI']
    defaultResourceUnit = os.environ['RESOURCE_UNIT']
    defaultDateUnit = os.environ['DATE_UNIT']
    staticFiles = os.environ['STATIC_FILES']


