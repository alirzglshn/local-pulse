from pymongo import GEOSPHERE , TEXT , ASCENDING , DESCENDING
from . db import get_db

def create_indexes():
    db = get_db()

    # this enables $near and $geoWithin
    db.events.create_index([("location", GEOSPHERE)])


    # this enables $text queries across title, description, tags for text search 
    db.events.create_index([
        ("title" , TEXT),
        ("description" , TEXT),
        ("tags" , TEXT),

    ] , name="event_text_index") 


    # category + date filtering 
    db.events.create_index([
        ("category" , ASCENDING),
        ("event_date" , DESCENDING), 
    ])

    # status "active" filtering 
    db.events.create_index([("status" , ASCENDING)]) 

    print("indexes created")


    