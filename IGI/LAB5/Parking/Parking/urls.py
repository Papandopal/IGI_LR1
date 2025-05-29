"""
URL configuration for Parking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from parking.views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('client/', client_dashboard, name='client_dashboard'),
    path('employee/', employee_dashboard, name='employee_dashboard'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('update_spot_price/<int:spot_id>/', update_spot_price, name='update_spot_price'),
    path('biggest_debtor/', biggest_debtor, name='biggest_debtor'),
    path('cars_with_multiple_owners/', cars_with_multiple_owners, name='cars_with_multiple_owners'),
    path('car_with_min_debt/', car_with_min_debt, name='car_with_min_debt'),
    path('total_debt/', total_debt, name='total_debt'),
    path('cars_by_brand/', cars_by_brand, name='cars_by_brand'),
    path('login/', CustomLoginView.as_view(template_name='parking/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    # CRUD для Client
    path('clients/create/', ClientCreateView.as_view(), name='client_create'),
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/<int:pk>/update/', ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client_delete'),
    # CRUD для Car
    path('cars/create/', CarCreateView.as_view(), name='car_create'),
    path('cars/', CarListView.as_view(), name='car_list'),
    path('cars/<int:pk>/update/', CarUpdateView.as_view(), name='car_update'),
    path('cars/<int:pk>/delete/', CarDeleteView.as_view(), name='car_delete'),
    # CRUD для ParkingSpot
    path('parkingspots/create/', ParkingSpotCreateView.as_view(), name='parkingspot_create'),
    path('parkingspots/', ParkingSpotListView.as_view(), name='parkingspot_list'),
    path('parkingspots/<int:pk>/update/', ParkingSpotUpdateView.as_view(), name='parkingspot_update'),
    path('parkingspots/<int:pk>/delete/', ParkingSpotDeleteView.as_view(), name='parkingspot_delete'),
    # Занятие и освобождение парковочного места
    path('parkingspots/<int:spot_id>/occupy/', occupy_spot, name='occupy_spot'),
    path('parkingspots/<int:spot_id>/free/', free_parking_spot, name='free_parking_spot'),
    # Оплата счета
    path('invoices/<int:invoice_id>/pay/', pay_invoice, name='pay_invoice'),
    path('about/', about_company, name='about_company'),
    path('news/', news, name='news'),
    path('terms/', terms_dictionary, name='terms_dictionary'),
    path('contacts/', contacts, name='contacts'),
    path('privacy/', privacy_policy, name='privacy_policy'),
    path('vacancies/', vacancies, name='vacancies'),
    path('reviews/', reviews, name='reviews'),
]