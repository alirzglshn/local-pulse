from bson import ObjectId
from datetime import datetime

# mongoDB returns Objectid and datetime objects which aren't json-serializable by default. 


def serialize_doc(doc):
    if doc is None:
        return None
    
    doc["_id"] = str(doc["_id"]) 
    for key , value in doc.items:
        if isinstance(value , datetime):
            doc[key] = value.isoformat()
        elif isinstance(value , list):
            doc[key] = [
                serialize_doc(i) if isinstance(i , dict) else i 
                for i in value 
            ]
    return doc 