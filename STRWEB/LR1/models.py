from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
import datetime

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    a = datetime.date.today()
    age = models.DateField(default=datetime.date(a.year-18, a.month, a.day))
    timezone = models.CharField(max_length=100, default='Europe/Minsk')  # Например, 'Europe/Paris'
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Синхронизация с User
        if self.user:
            self.user.username = self.name
            self.user.email = self.email
            self.user.save()
        super().save(*args, **kwargs)

class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()

    def __str__(self):
        return self.name

class Car(models.Model):
    license_plate = models.CharField(max_length=20, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    clients = models.ManyToManyField(Client, related_name='cars')

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"

class ParkingSpot(models.Model):
    number = models.PositiveIntegerField(unique=True, validators=[MaxValueValidator(999)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_occupied = models.BooleanField(default=False)
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Место {self.number}"

class Invoice(models.Model):
    code = models.CharField(max_length=8, unique=True)
    car = models.ForeignKey('Car', on_delete=models.CASCADE)
    parking_spot = models.ForeignKey('ParkingSpot', on_delete=models.CASCADE)
    spot_price = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateField()
    payment_date = models.DateTimeField(null=True, blank=True)
    debt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания
    updated_at = models.DateTimeField(auto_now=True)     # Дата последнего изменения

    def __str__(self):
        return f"Invoice {self.code}"

class Income(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=200)

    def __str__(self):
        return f"Доход {self.amount} от {self.date}"

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return self.name

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    valid_until = models.DateField()

    def __str__(self):
        return self.code

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    valid_until = models.DateField()

    def __str__(self):
        return self.code
    
class Article(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=120, blank=True)
    author = models.CharField(max_length=120, default='Команда PARKING')
    tags = models.CharField(max_length=255, blank=True, help_text='Список тегов через запятую')
    content = models.TextField(blank=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def get_tags_list(self):
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

class Term(models.Model):
    term = models.CharField(max_length=100)
    definition = models.TextField()
    added_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.term

class EmployeeContact(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    photo_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class JobVacancy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    posted_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.rating} stars"

class Partner(models.Model):
    name = models.CharField(max_length=200)
    logo_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Banner(models.Model):
    title = models.CharField(max_length=200)
    image_url = models.URLField(blank=True, null=True)
    link_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title


class CompanyInfo(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    values = models.TextField(blank=True)
    logo_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    founded_year = models.PositiveIntegerField(default=2012)
    employees_count = models.PositiveIntegerField(default=0)
    clients_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CompanyHistory(models.Model):
    year = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['year', 'order']

    def __str__(self):
        return f"{self.year} — {self.title}"


class CompanyRequisite(models.Model):
    legal_name = models.CharField(max_length=255)
    inn = models.CharField(max_length=20, blank=True)
    kpp = models.CharField(max_length=20, blank=True)
    ogrn = models.CharField(max_length=20, blank=True)
    legal_address = models.CharField(max_length=255)
    actual_address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    bank_name = models.CharField(max_length=200, blank=True)
    bank_account = models.CharField(max_length=34, blank=True)
    correspondent_account = models.CharField(max_length=34, blank=True)
    bik = models.CharField(max_length=20, blank=True)
    director_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Реквизит компании"
        verbose_name_plural = "Реквизиты компании"

    def __str__(self):
        return self.legal_name


class CompanyCertificate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    issued_by = models.CharField(max_length=200, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    document_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'issued_date']

    def __str__(self):
        return self.name