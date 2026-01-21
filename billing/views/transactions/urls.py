from django.urls import path
from billing.views.transactions.views import ConversionView, ServiceSpendView, TopUpView


urlpatterns = [
    path('conversion/', ConversionView.as_view(), name='conversion'),
    path('service-spend/', ServiceSpendView.as_view(), name='service-spend'),
    path('account-topup/', TopUpView.as_view(), name='account-topup'),
]
