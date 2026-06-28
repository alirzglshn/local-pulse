# LocalPulse 

A real-time city events analytics API built with Django and MongoDB Atlas.
Demonstrates advanced MongoDB patterns including aggregation pipelines,
geospatial queries, full-text search, and embedded document design.

## Tech Stack

- **Backend:** Django + Django REST Framework
- **Database:** MongoDB Atlas (PyMongo)
- **Search:** MongoDB Atlas Search (Apache Lucene)
- **Deployment:** Railway

## MongoDB Features Showcased

| Feature | Where |
|---|---|
| Embedded documents & arrays | Event schema — attendees, comments, location |
| `$push` + `$inc` (atomic writes) | Join event endpoint |
| `$elemMatch` | Duplicate join prevention |
| Aggregation pipelines | Trending tags, neighborhood heatmap |
| `$unwind` → `$group` → `$facet` | Tag frequency & analytics |
| `2dsphere` index | Geospatial indexing |
| `$near` | Radius-based proximity search |
| `$geoWithin` | Polygon area filtering |
| Atlas Search + `lucene.english` | Stemmed full-text search |
| Fuzzy matching | Typo-tolerant queries |
| Faceted search | Category/city/popularity counts |
| Autocomplete | edgeGram tokenization |

## API Endpoints

### Events
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/events/` | Create an event |
| `GET` | `/api/events/<id>/` | Get event detail |
| `POST` | `/api/events/<id>/join/` | Join an event |

### Geospatial
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/events/near/` | Events within radius (`?lat=&lng=&radius_km=`) |
| `POST` | `/api/events/within-area/` | Events inside a polygon |

### Search
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/events/search/` | Full-text search with fuzzy matching |
| `GET` | `/api/events/search/facets/` | Faceted search with category/city counts |
| `GET` | `/api/events/search/autocomplete/` | Search-as-you-type suggestions |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/events/analytics/trending-tags/` | Top tags by period (`?days=7`) |
| `GET` | `/api/events/analytics/neighborhood-heatmap/` | Event density per neighborhood |

## Local Setup

```bash
git clone https://github.com/yourname/localpulse
cd localpulse
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your MONGO_URI
python seed.py         # seed 200 realistic events
python manage.py runserver
```

## Environment Variables

```
MONGO_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
MONGO_DB_NAME=localpulse
```