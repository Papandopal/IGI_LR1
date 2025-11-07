from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *

# Регистрация моделей в админке
admin.site.register(Client)
admin.site.register(Car)
admin.site.register(ParkingSpot)
admin.site.register(Invoice)
admin.site.register(Income)
admin.site.register(Service)
admin.site.register(ServiceCategory)
admin.site.register(PromoCode)
admin.site.register(Coupon)
admin.site.register(Employee)
admin.site.register(Article)
admin.site.register(Term)
admin.site.register(EmployeeContact)
admin.site.register(JobVacancy)
admin.site.register(Review)
admin.site.register(Partner)
admin.site.register(Banner)
admin.site.register(CompanyInfo)
admin.site.register(CompanyHistory)
admin.site.register(CompanyRequisite)
admin.site.register(CompanyCertificate)
# Функция для создания групп (вызов убрали)
def create_groups():
    Group.objects.get_or_create(name='Client')
    Group.objects.get_or_create(name='Employee')

create_groups()