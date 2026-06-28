from django.urls import path
from . import views

urlpatterns = [
    path("health/",                         views.health_check),
    path("",                                views.create_event),
    path("near/",                           views.events_near_me),
    path("within-area/",                    views.events_within_area),
    path("search/",                         views.search_events),
    path("search/facets/",                  views.search_events_faceted),
    path("search/autocomplete/",            views.autocomplete_events),
    path("<str:event_id>/",                 views.get_event),
    path("<str:event_id>/join/",            views.join_event),
    path("analytics/trending-tags/",        views.trending_tags),
    path("analytics/neighborhood-heatmap/", views.neighborhood_heatmap),
]