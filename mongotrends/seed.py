import os
import random
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient

load_dotenv()

fake    = Faker()
client  = MongoClient(os.getenv("MONGO_URI"))
db      = client[os.getenv("MONGO_DB_NAME")]

# ── Config ────────────────────────────────────────────────────────────────────

CATEGORIES = ["music", "food", "sports", "tech", "community", "art"]

TAGS_BY_CATEGORY = {
    "music":     ["jazz", "live-music", "outdoor", "free", "band", "acoustic", "DJ", "concert"],
    "food":      ["street-food", "vegan", "market", "brunch", "popup", "tasting", "bbq"],
    "sports":    ["running", "cycling", "yoga", "football", "basketball", "free", "tournament"],
    "tech":      ["hackathon", "meetup", "AI", "startup", "workshop", "networking", "open-source"],
    "community": ["volunteering", "cleanup", "fundraiser", "kids", "free", "neighborhood"],
    "art":       ["exhibition", "gallery", "photography", "mural", "workshop", "free", "pop-up"],
}

# Real neighborhoods with real coordinates [lng, lat]
NEIGHBORHOODS = [
    {"name": "Upper West Side",  "city": "New York",    "coords": [-73.9812, 40.7870]},
    {"name": "Williamsburg",     "city": "New York",    "coords": [-73.9571, 40.7081]},
    {"name": "Astoria",          "city": "New York",    "coords": [-73.9304, 40.7721]},
    {"name": "Silver Lake",      "city": "Los Angeles", "coords": [-118.2717, 34.0870]},
    {"name": "Venice Beach",     "city": "Los Angeles", "coords": [-118.4695, 33.9850]},
    {"name": "Mission District", "city": "San Francisco","coords":[-122.4194, 37.7599]},
    {"name": "Hayes Valley",     "city": "San Francisco","coords":[-122.4247, 37.7759]},
    {"name": "Wicker Park",      "city": "Chicago",     "coords": [-87.6826, 41.9088]},
    {"name": "Logan Square",     "city": "Chicago",     "coords": [-87.7034, 41.9217]},
    {"name": "Capitol Hill",     "city": "Seattle",     "coords": [-122.3201, 47.6253]},
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def jitter(coord, delta=0.015):
    """Add slight randomness so events don't all stack on one point."""
    return coord + random.uniform(-delta, delta)

def random_future_date(days_ahead=90):
    offset = random.randint(1, days_ahead)
    return datetime.now(timezone.utc) + timedelta(days=offset)

def make_attendees(n):
    return [
        {
            "user_id":   fake.uuid4(),
            "name":      fake.first_name() + " " + fake.last_name()[0] + ".",
            "joined_at": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
        }
        for _ in range(n)
    ]

def make_comments(n):
    phrases = [
        "Can't wait for this!", "See you there!", "Bringing my friends.",
        "Is there parking nearby?", "Loved this last time.",
        "How long does it run?", "Free entry?", "This looks amazing.",
    ]
    return [
        {
            "user_id":   fake.uuid4(),
            "text":      random.choice(phrases),
            "posted_at": datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72)),
        }
        for _ in range(n)
    ]

# ── Build documents ───────────────────────────────────────────────────────────

def make_event():
    category    = random.choice(CATEGORIES)
    tags        = random.sample(TAGS_BY_CATEGORY[category], k=random.randint(2, 4))
    hood        = random.choice(NEIGHBORHOODS)
    attendee_n  = random.randint(0, 120)
    now         = datetime.now(timezone.utc)

    return {
        "title":          fake.catch_phrase().title(),
        "description":    fake.paragraph(nb_sentences=4),
        "category":       category,
        "status":         random.choices(["active", "completed"], weights=[85, 15])[0],
        "tags":           tags,
        "event_date":     random_future_date(),
        "duration_hours": random.choice([1, 2, 3, 4, 6, 8]),
        "location": {
            "type":         "Point",
            "coordinates":  [jitter(hood["coords"][0]), jitter(hood["coords"][1])],
            "address":      fake.street_address(),
            "city":         hood["city"],
            "neighborhood": hood["name"],
        },
        "attendees":      make_attendees(attendee_n),
        "comments":       make_comments(random.randint(0, 6)),
        "attendee_count": attendee_n,
        "view_count":     random.randint(10, 800),
        "created_at":     now - timedelta(days=random.randint(1, 60)),
        "updated_at":     now,
    }

# ── Run ───────────────────────────────────────────────────────────────────────

def seed(n=200):
    db.events.drop()
    print(f"Seeding {n} events...")
    events = [make_event() for _ in range(n)]
    db.events.insert_many(events)
    print(f"✅ {n} events inserted into '{db.name}.events'")
    print(f"   Cities:     {', '.join(set(e['location']['city'] for e in events))}")
    print(f"   Categories: {', '.join(set(e['category'] for e in events))}")

if __name__ == "__main__":
    seed(200)