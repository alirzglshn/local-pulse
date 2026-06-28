
EVENT_DOCUMENT = {
    
    "title":       "Jazz Night at Riverside Park",
    "description": "Live jazz performances by local artists every Friday evening.",
    "status":      "active",          # active | cancelled | completed
    "created_at":  "ISODate(...)",
    "updated_at":  "ISODate(...)",

    # location info
    # GeoJSON format 

    "location": {
        "type":        "Point",
        "coordinates": [-74.0060, 40.7128],   # [longitude, latitude]
        "address":     "Riverside Park, Manhattan",
        "city":        "New York",
        "neighborhood":"Upper West Side",
    },

    # arrays
    "tags": ["jazz", "music", "outdoor", "free"],   # for full-text + filtering

    "attendees": [                                   # embedded
        {
            "user_id":   "abc123",                   # could be a UUID or username
            "name":      "Sarah K.",
            "joined_at": "ISODate(...)",
        }
    ],

    "comments": [                        #  also embedded since it won't be accessed independently
        {
            "user_id":    "xyz789",
            "text":       "Can't wait for this!",
            "posted_at":  "ISODate(...)",
        }
    ],

    # analytics
    "view_count":     142,
    "attendee_count": 38,        
    "category":       "music",   

    # time info
    "event_date":     "ISODate(...)",
    "duration_hours": 3,
}

USER_DOCUMENT = {
    "username":   "sarah_k",
    "email":      "sarah@example.com",
    "created_at": "ISODate(...)",

    # this is also embedded  — no separate table needed
    "preferences": {
        "categories":    ["music", "food"],
        "city":          "New York",
        "max_radius_km": 10,
    },

    # store IDs
    "saved_events": ["<ObjectId>", "<ObjectId>"],
}