from django.urls import include, path


api_patterns = [
    path("transactions/", include("billing.views.transactions.urls")),
]


urlpatterns = [
    path("api/", include(api_patterns)),
]
