from django.shortcuts import render
from mongotrends.db import get_db
from django.http import JsonResponse
import json 
from datetime import datetime , timezone 
from bson import objectid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from mongotrends.db import get_db
from .utils import serialize_doc




def health_check(request):
    db = get_db()
    db.client.admin.command("ping")
    return JsonResponse({"status":"ok" , "db": db.name})



@csrf_exempt
@require_http_methods(["POST"])
def create_event(request):
    db = get_db()
    
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error" : "Invalid JSON"} , status=400)
    
    required  = ["title" , "description" , "category" , "event_date" , "location" , "tags"]
    missing = [f for f in required if f not in body ] 
    if missing :
        return JsonResponse({"error":f"Missing fields : {missing}"} , status=400)
    
    now  = datetime.now(timezone.utc)

    document = {
        "title":   body["title"] ,
        "description": body["description"],
        "category" : body["category"] ,
        "status" : "active" , 
        "tags" : body.get("tags" , []) ,
        "event_date" : datetime.fromisoformat(body["event_date"]),
        "duration_hours" : body.get("duration_hours" , 2),

        "location":{
            "type":"Point" , 
            "coordinates": body["location"]["coordinates"],
            "address" : body["location"].get("address" , ""),
            "city" : body["location"].get("city" , ""), 
            "neighborhood" : body["location"].get("neighborhood" , ""),

        } , 
        "attendees": [] , 
        "comments": [] , 
        "attendee_count" : 0 , 
        "view_count" : 0 ,
        "created_at" : now , 
        "updated_at" : now , 
    }

    result = db.events.insert_one(document)
    document["_id"] =str(result.inserted_id)

    return JsonResponse({"message" : "Event created" , "event_id":document["_id"]} , status=201)





# getting events 

@require_http_methods(["GET"])
def get_event(request , event_id):
    db = get_db()
    try:
        doc = db.events.find_one({"_id": objectid(event_id)})
    except Exception:
        return JsonResponse({"error":"Invalid event ID"} , status=400)

    if not doc:
        return JsonResponse({"error":"Event not found"} , status=404) 
    

    db.events.update_one(
        {"_id": objectid(event_id)},
        {"$inc":{"views_count":1}}
    )

    return JsonResponse(serialize_doc(doc))      


#joining events 

@csrf_exempt
@require_http_methods(["POST"])
def join_event(request, event_id):
    db = get_db()
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_id  = body.get("user_id")
    username = body.get("username")
    if not user_id or not username:
        return JsonResponse({"error": "user_id and username required"}, status=400)

    try:
        oid = objectid(event_id)
    except Exception:
        return JsonResponse({"error": "Invalid event ID"}, status=400)

    # Checking if already joined — $elemMatch queries inside arrays
    already_joined = db.events.find_one({
        "_id": oid,
        "attendees": {"$elemMatch": {"user_id": user_id}}
    })
    if already_joined:
        return JsonResponse({"error": "Already joined"}, status=409)

    # $push into array + $inc counter — single atomic write
    result = db.events.update_one(
        {"_id": oid, "status": "active"},
        {
            "$push": {"attendees": {
                "user_id":   user_id,
                "name":      username,
                "joined_at": datetime.now(timezone.utc),
            }},
            "$inc":  {"attendee_count": 1},
            "$set":  {"updated_at": datetime.now(timezone.utc)},
        }
    )

    if result.matched_count == 0:
        return JsonResponse({"error": "Event not found or not active"}, status=404)

    return JsonResponse({"message": f"{username} joined the event!"})



# trendings - turning tags into documents 
@require_http_methods(["GET"])
def trending_tags(request):

    db = get_db()
    days = int(request.GET.get("days" , 7))
    since = datetime.now(timezone.utc).replace(
        hour=0 , minute=0 , second=0 , microsecond=0
    )

    from datetime import timedelta

    since  = since - timedelta(days=days)

    pipeline = [

        #  recent & active events
        {"$match":{
            "status": "active",
            "created_at" :{"$gte":since}, 
        }},


         # exploding the tags array: one doc per tag
        {"$unwind":"$tags"},

         # counting how many events each tag appears in
        {"$group":{
            "_id": "$tags" , 
            "event_count":{"$sum" : 1},
            "total_views" :{"$sum" : "$view_count"} , 

        }} , 

        # sorting by event count descending
        {"$sort" : {"event_count" : -1}}, 


        # top 10
        {"$limit": 10} , 

        # reshape output to be clean 
        {"$project":{
            "_id":   0 , 
            "tag" : "$_id" , 
            "event_count" : 1 , 
            "total_views": 1 , 
        }},
    ]

    results = list(db.events.aggregate(pipeline))
    return JsonResponse({"trending_tags":results  , "period_days": days})



# find nearest events
@require_http_methods(["GET"])
def events_near_me(request):
    db = get_db()

    # Expect ?lat=40.7128&lng=-74.0060&radius_km=5&category=music
    try:
        lat       = float(request.GET.get("lat"))
        lng       = float(request.GET.get("lng"))
        radius_km = float(request.GET.get("radius_km", 5))
    except (TypeError, ValueError):
        return JsonResponse({"error": "lat, lng are required and must be numbers"}, status=400)
 
    max_distance_meters = radius_km * 1000

    # Base geospatial filter
    query = {
        "status": "active",
        "location": {
            "$near": {
                "$geometry": {
                    "type":        "Point",
                    "coordinates": [lng, lat],   # longitude first — always
                },
                "$maxDistance": max_distance_meters,
            }
        }
    }

    # Optional category filter stacked on top
    category = request.GET.get("category")
    if category:
        query["category"] = category

    # Optional date filter — only future events
    upcoming_only = request.GET.get("upcoming", "true").lower() == "true"
    if upcoming_only:
        query["event_date"] = {"$gte": datetime.now(timezone.utc)}

    # Project only what the frontend needs — don't send full attendees array
    projection = {
        "title":           1,
        "category":        1,
        "event_date":      1,
        "attendee_count":  1,
        "view_count":      1,
        "tags":            1,
        "location":        1,
        "status":          1,
    }

    events = list(db.events.find(query, projection).limit(20))
    events = [serialize_doc(e) for e in events]

    return JsonResponse({
        "count":     len(events),
        "radius_km": radius_km,
        "events":    events,
    })


# find events within a specific area 
@csrf_exempt
@require_http_methods(["POST"])
def events_within_area(request):
    db = get_db()

    # Expects a GeoJSON Polygon in the request body
    # { "polygon": { "coordinates": [[[lng,lat], [lng,lat], ...]] } }
    try:
        body    = json.loads(request.body)
        polygon = body["polygon"]
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "polygon is required"}, status=400)

    # Validate polygon is closed — first and last coordinate must match
    coords = polygon.get("coordinates", [[]])[0]
    if coords[0] != coords[-1]:
        return JsonResponse(
            {"error": "Polygon must be closed — first and last coordinate must match"},
            status=400
        )

    query = {
        "status": "active",
        "location": {
            "$geoWithin": {
                "$geometry": {
                    "type":        "Polygon",
                    "coordinates": polygon["coordinates"],
                }
            }
        }
    }

    # Stack a date range filter if provided
    date_from = body.get("date_from")
    date_to   = body.get("date_to")
    if date_from or date_to:
        query["event_date"] = {}
        if date_from:
            query["event_date"]["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            query["event_date"]["$lte"] = datetime.fromisoformat(date_to)

    events = list(db.events.find(query, {
        "title": 1, "category": 1, "event_date": 1,
        "attendee_count": 1, "location": 1, "tags": 1,
    }).sort("event_date", 1))

    events = [serialize_doc(e) for e in events]

    return JsonResponse({"count": len(events), "events": events})




@require_http_methods(["GET"])
def neighborhood_heatmap(request):
    db = get_db()

    pipeline = [
        # Only active, future events
        {"$match": {
            "status":     "active",
            "event_date": {"$gte": datetime.now(timezone.utc)},
        }},

        # Group by neighborhood — count events, sum attendees
        {"$group": {
            "_id":             "$location.neighborhood",
            "event_count":     {"$sum": 1},
            "total_attendees": {"$sum": "$attendee_count"},
            "total_views":     {"$sum": "$view_count"},
            "categories":      {"$addToSet": "$category"},  # unique categories per neighborhood

            # Grab the coordinates of the first event as a representative point
            "sample_coordinates": {"$first": "$location.coordinates"},
        }},

        {"$sort": {"event_count": -1}},

        {"$project": {
            "_id":              0,
            "neighborhood":     "$_id",
            "event_count":      1,
            "total_attendees":  1,
            "total_views":      1,
            "categories":       1,
            "coordinates":      "$sample_coordinates",  # [lng, lat] for map pin
        }},
    ]

    results = list(db.events.aggregate(pipeline))
    return JsonResponse({"neighborhoods": results})


@require_http_methods(["GET"])
def search_events(request):
    db = get_db()

    query_text = request.GET.get("q", "").strip()
    if not query_text:
        return JsonResponse({"error": "Query parameter 'q' is required"}, status=400)

    # Optional filters
    category = request.GET.get("category")
    city     = request.GET.get("city")
    page     = int(request.GET.get("page", 1))
    per_page = int(request.GET.get("per_page", 10))
    skip     = (page - 1) * per_page

    # $search must always be the very first stage in the pipeline
    pipeline = [
        {"$search": {
            "index": "event_search_index",
            "compound": {
                "must": [
                    # Full-text search across title, description, tags
                    # fuzzy allows 1 character typo — "jaz" matches "jazz"
                    {"text": {
                        "query": query_text,
                        "path":  ["title", "description", "tags"],
                        "fuzzy": {"maxEdits": 1},
                        "score": {"boost": {
                            "path": "attendee_count",   # popular events rank higher
                        }}
                    }}
                ],
                "filter": [
                    {"text": {"query": "active", "path": "status"}},
                    # Dynamically add category/city filters below
                    *([{"text": {"query": category, "path": "category"}}] if category else []),
                    *([{"text": {"query": city,     "path": "location.city"}}] if city else []),
                ]
            }
        }},

        # Add relevance score to each result
        {"$addFields": {
            "search_score": {"$meta": "searchScore"}
        }},

        # Only return future active events
        {"$match": {
            "event_date": {"$gte": datetime.now(timezone.utc)},
        }},

        # Clean projection — don't expose full attendees array
        {"$project": {
            "title":          1,
            "description":    1,
            "category":       1,
            "tags":           1,
            "event_date":     1,
            "attendee_count": 1,
            "location":       1,
            "search_score":   1,
        }},

        {"$skip":  skip},
        {"$limit": per_page},
    ]

    results = list(db.events.aggregate(pipeline))
    results = [serialize_doc(r) for r in results]

    return JsonResponse({
        "query":    query_text,
        "page":     page,
        "count":    len(results),
        "results":  results,
    })




@require_http_methods(["GET"])
def search_events_faceted(request):
    db = get_db()

    query_text = request.GET.get("q", "").strip()
    if not query_text:
        return JsonResponse({"error": "Query parameter 'q' is required"}, status=400)

    pipeline = [
        {"$searchMeta": {
            "index": "event_search_index",
            "facet": {
                "operator": {
                    "compound": {
                        "must": [{"text": {
                            "query": query_text,
                            "path":  ["title", "description", "tags"],
                            "fuzzy": {"maxEdits": 1},
                        }}],
                        "filter": [
                            {"text": {"query": "active", "path": "status"}}
                        ]
                    }
                },
                "facets": {
                    # How many results per category?
                    "category_facet": {
                        "type":  "string",
                        "path":  "category",
                        "numBuckets": 10,
                    },
                    # How many results per city?
                    "city_facet": {
                        "type":  "string",
                        "path":  "location.city",
                        "numBuckets": 10,
                    },
                    # Bucket events by attendee count ranges
                    "popularity_facet": {
                        "type": "number",
                        "path": "attendee_count",
                        "boundaries": [0, 10, 50, 100, 500],
                        "default": "500+",
                    },
                }
            }
        }},
    ]

    result     = list(db.events.aggregate(pipeline))
    facet_data = result[0] if result else {}

    return JsonResponse({
        "query":  query_text,
        "count":  facet_data.get("count", {}).get("lowerBound", 0),
        "facets": facet_data.get("facets", {}),
    })



@require_http_methods(["GET"])
def autocomplete_events(request):
    db = get_db()

    prefix = request.GET.get("q", "").strip()
    if len(prefix) < 2:
        return JsonResponse({"suggestions": []})

    pipeline = [
        {"$search": {
            "index": "event_search_index",
            "autocomplete": {
                "query": prefix,
                "path":  "title",
                "fuzzy": {"maxEdits": 1},
            }
        }},
        {"$limit": 5},
        {"$project": {
            "title":    1,
            "category": 1,
            "_id":      1,
        }},
    ]

    results = list(db.events.aggregate(pipeline))
    results = [serialize_doc(r) for r in results]

    return JsonResponse({"suggestions": results})