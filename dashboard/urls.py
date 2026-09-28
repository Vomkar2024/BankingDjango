from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('transfer/', views.transfer_money, name='transfer_money'),
    path('pay-bill/', views.pay_bill, name='pay_bill'),
    path('deposit/', views.deposit_funds, name='deposit_funds'),
    path('withdraw/', views.withdraw_funds, name='withdraw_funds'),
    path('cards/<int:card_id>/toggle-freeze/', views.toggle_card_freeze, name='toggle_card_freeze'),
    path('cards/<int:card_id>/toggle-contactless/', views.toggle_contactless, name='toggle_contactless'),
    path('cards/', views.cards_view, name='cards_view'),
    path('loans/', views.loans_view, name='loans_view'),
    path('transactions/', views.transactions_view, name='transactions_view'),
    path('support/', views.support_view, name='support_view'),
    path('support/create/', views.create_ticket, name='create_ticket'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
]
