from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.db.models import Sum, Count, Q, F
from django.http import Http404
from django.utils import timezone
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
import calendar
import logging
import requests
from django.contrib.auth import logout
from .models import *
from django.urls import reverse_lazy
from .forms import SignUpForm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from django.db.models.functions import TruncDate

# Настройка логирования
logger = logging.getLogger(__name__)

news_photo = ['images/news1.jpeg', 'images/news2.jpeg', 'images/news3.jpeg', 'images/news4.png']
workers = ['images/workers1.jpeg', 'images/workers2.jpeg', 'images/workers3.jpeg', 'images/workers4.jpeg']

# Проверка ролей пользователя
def is_admin(user):
    return user.is_authenticated and user.is_superuser

def is_employee(user):
    return user.is_authenticated and user.groups.filter(name='Employee').exists()

def is_client(user):
    return user.is_authenticated and user.groups.filter(name='Client').exists()

def is_client_or_admin(user):
    return is_client(user) or is_admin(user)

# Кастомный LoginView для динамического перенаправления
class CustomLoginView(LoginView):
    template_name = 'parking/login.html'

    def get_success_url(self):
        user = self.request.user
        
        if user.is_superuser:
            return '/admin_dashboard/'
        elif is_client(user):
            return '/client/'
        elif is_employee(user):
            return '/employee/'
        return '/home/'

    def form_valid(self, form):
        user = form.get_user()
        if is_client(user):
            Client.objects.get_or_create(
                user=user,
                defaults={'name': user.username, 'email': user.email or f"{user.username}@example.com"}
            )
        elif is_employee(user):
            Employee.objects.get_or_create(
                user=user,
                defaults={'name': user.username, 'email': user.email or f"{user.username}@example.com"}
            )
        return super().form_valid(form)

# Представление для регистрации
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'parking/signup.html'
    success_url = reverse_lazy('client_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        return response

# Главная страница (доступна всем)
def home(request):
    categories = ServiceCategory.objects.all()
    services = Service.objects.all()
    promo_codes = PromoCode.objects.filter(valid_until__gte=timezone.now())
    coupons = Coupon.objects.filter(valid_until__gte=timezone.now())

    category_filter = request.GET.get('category')
    price_sort = request.GET.get('price_sort')
    search_query = request.GET.get('search', '').strip()
    if category_filter:
        services = services.filter(category__name=category_filter)
        categories = ServiceCategory.objects.filter(service__in=services).distinct()
    if search_query:
        services = services.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    if price_sort:
        services = services.order_by('price' if price_sort == 'asc' else '-price')

    try:
        joke_response = requests.get('https://official-joke-api.appspot.com/random_joke')
        joke = joke_response.json() if joke_response.status_code == 200 else {'setup': 'Не удалось загрузить шутку', 'punchline': ''}
    except requests.RequestException:
        joke = {'setup': 'Не удалось загрузить шутку', 'punchline': ''}

    try:
        quote_response = requests.get('https://favqs.com/api/qotd')
        quote = quote_response.json()['quote'] if quote_response.status_code == 200 else {'body': 'Не удалось загрузить цитату', 'author': 'Неизвестен'}
    except requests.RequestException:
        quote = {'body': 'Не удалось загрузить цитату', 'author': 'Неизвестен'}

    total_profit = Invoice.objects.aggregate(total=Sum('spot_price'))['total'] or 0
    parking_rentals = Invoice.objects.values('parking_spot').annotate(total=Sum('spot_price')).order_by('-total')
    most_profitable_spot = parking_rentals.first()['parking_spot'] if parking_rentals.exists() else None
    most_profitable_spot_profit = parking_rentals.first()['total'] if parking_rentals.exists() else 0

    rental_amounts = list(Invoice.objects.values_list('spot_price', flat=True))
    if rental_amounts:
        avg_rental = sum(rental_amounts) / len(rental_amounts)
        sorted_rentals = sorted(rental_amounts)
        median_rental = (sorted_rentals[len(sorted_rentals) // 2 - 1] + sorted_rentals[len(sorted_rentals) // 2]) / 2 if len(sorted_rentals) % 2 == 0 else sorted_rentals[len(sorted_rentals) // 2]
        mode_rental = max(set(rental_amounts), key=rental_amounts.count)
    else:
        avg_rental = median_rental = mode_rental = 0

    client_ages_dates = list(Client.objects.values_list('age', flat=True))
    client_ages = []
    
    
    for item in client_ages:
        if item:
            client_ages.append((datetime.date.today() - item).days // 365)
    
    avg_age = sum(client_ages) / len(client_ages) if client_ages else 0
    sorted_ages = sorted(client_ages)
    median_age = (sorted_ages[len(sorted_ages) // 2 - 1] + sorted_ages[len(sorted_ages) // 2]) / 2 if len(sorted_ages) % 2 == 0 and sorted_ages else sorted_ages[len(sorted_ages) // 2] if sorted_ages else 0

    all_news = list(Article.objects.all())
    last_new = all_news[-1] if all_news else None
    
    # Получаем активных партнеров
    partners = Partner.objects.filter(is_active=True).order_by('name')
    
    # Получаем активные баннеры
    banners = Banner.objects.filter(is_active=True).order_by('order', 'created_at')

    return render(request, 'parking/home.html', {
        'categories': categories,
        'services': services,
        'promo_codes': promo_codes,
        'coupons': coupons,
        'joke': joke,
        'quote': quote,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
        'total_profit': total_profit,
        'most_profitable_spot': most_profitable_spot,
        'most_profitable_spot_profit': most_profitable_spot_profit,
        'avg_rental': avg_rental,
        'median_rental': median_rental,
        'mode_rental': mode_rental,
        'avg_age': avg_age,
        'median_age': median_age,
        'category_filter': category_filter,
        'price_sort': price_sort,
        'search_query': search_query,
        'last_new': last_new,
        'partners': partners,
        'banners': banners,
    })

# Кастомный выход
def custom_logout(request):
    logout(request)
    return redirect('home')

# Страница клиента (доступна только зарегистрированным клиентам)
@login_required
@user_passes_test(is_client)
def client_dashboard(request):
    if not is_client(request.user):
        return redirect('home')
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        client = Client.objects.create(
            user=request.user,
            name=request.user.username,
            email=request.user.email or f"{request.user.username}@example.com",
            age=18,
            timezone='Europe/Minsk'
        )
    cars = client.cars.all()
    invoices = Invoice.objects.filter(car__in=cars).order_by('-issue_date')
    parking_spots = ParkingSpot.objects.all()

    now_utc = datetime.datetime.utcnow()
    today = now_utc.date()
    cal = calendar.monthcalendar(today.year, today.month)

    now = datetime.datetime.now(ZoneInfo(client.timezone))
    offset_hours = now.utcoffset().total_seconds() / 3600
    now_local = now_utc + timedelta(hours=offset_hours)

    return render(request, 'parking/client_dashboard.html', {
        'client': client,
        'cars': cars,
        'invoices': invoices,
        'parking_spots': parking_spots,
        'current_date_utc': now_utc,
        'current_date_local': now_local,
        'client_timezone': f"{client.timezone} (UTC{'+' if offset_hours >= 0 else ''}{offset_hours})",
        'calendar': cal,
        'month': today.month,
        'year': today.year,
        'today_day': today.day,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

def about_company(request):
    company_info = CompanyInfo.objects.filter(is_active=True).order_by('-updated_at').first()
    history_items = CompanyHistory.objects.filter(is_active=True).order_by('year')
    requisites = CompanyRequisite.objects.filter(is_active=True).order_by('-created_at')
    certificates = CompanyCertificate.objects.filter(is_active=True).order_by('order', 'issued_date')

    return render(request, 'parking/about_company.html', {
        'company_info': company_info,
        'history_items': history_items,
        'requisites': requisites,
        'certificates': certificates,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })


def news(request):
    articles = Article.objects.all().order_by('-created_at')
    search_query = request.GET.get('search', '').strip()
    current_category = request.GET.get('category', '').strip()

    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    if current_category:
        articles = articles.filter(category__iexact=current_category)

    categories = Article.objects.exclude(category="").values_list('category', flat=True).distinct()
    featured_articles = articles.order_by('-views_count', '-created_at')[:2]

    context = {
        'articles': articles,
        'featured_articles': featured_articles,
        'categories': categories,
        'current_category': current_category,
        'search_query': search_query,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    }
    return render(request, 'parking/news.html', context)


def news_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    Article.objects.filter(pk=pk).update(views_count=F('views_count') + 1)
    article.refresh_from_db()
    return render(request, 'parking/news_detail.html', {
        'article': article,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Страница словаря терминов
def terms_dictionary(request):
    terms = Term.objects.all().order_by('-added_date')
    search_query = request.GET.get('search', '').strip()
    if search_query:
        terms = terms.filter(
            Q(term__icontains=search_query) |
            Q(definition__icontains=search_query)
        )
    return render(request, 'parking/terms_dictionary.html', {
        'terms': terms,
        'search_query': search_query,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Страница контактов
def contacts(request):
    employees = EmployeeContact.objects.all()
    return render(request, 'parking/contacts.html', {
        'employees': employees,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Страница политики конфиденциальности
def privacy_policy(request):
    return render(request, 'parking/privacy_policy.html', {
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Страница вакансий
def vacancies(request):
    jobs = JobVacancy.objects.all().order_by('-posted_date')
    return render(request, 'parking/vacancies.html', {
        'jobs': jobs,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Страница отзывов (доступна клиентам и админам)
@login_required
@user_passes_test(is_client_or_admin)
def reviews(request):
    if not is_client_or_admin(request.user):
        return redirect('home')
    if is_admin(request.user):
        reviews = Review.objects.all().order_by('-created_at')
    else:
        reviews = Review.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        if is_client(request.user):
            text = request.POST.get('text')
            rating = request.POST.get('rating')
            if text and rating:
                Review.objects.create(user=request.user, text=text, rating=rating)
                return redirect('reviews')
        else:
            return render(request, 'parking/error.html', {'message': 'Только клиенты могут добавлять отзывы'})
    return render(request, 'parking/reviews.html', {
        'reviews': reviews,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Обновление профиля клиента
class ClientUpdateView(UpdateView):
    model = Client
    fields = ['name', 'email', 'age', 'timezone']
    template_name = 'parking/client_form.html'
    success_url = reverse_lazy('client_dashboard')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if is_admin(user) or (is_client(user) and obj.user == user):
            return obj
        raise Http404("У вас нет доступа к редактированию этого клиента")

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect('client_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

# Оплата счета клиентом
@login_required
@user_passes_test(is_client)
def pay_invoice(request, invoice_id):
    if not is_client(request.user):
        return redirect('home')

    invoice = get_object_or_404(Invoice, id=invoice_id)
    client = Client.objects.get(user=request.user)
    if invoice.car not in client.cars.all():
        return render(request, 'parking/error.html', {'message': 'Этот счёт вам не принадлежит'})
    if request.method == 'POST':
        invoice.payment_date = timezone.now()
        invoice.debt = 0
        invoice.save()
        return redirect('client_dashboard')
    return render(request, 'parking/pay_invoice_confirm.html', {
        'invoice': invoice,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Страница сотрудника (доступна только сотрудникам)
@login_required
@user_passes_test(is_employee)
def employee_dashboard(request):
    if not is_employee(request.user):
        return redirect('home')

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = Employee.objects.create(
            user=request.user,
            name=request.user.username,
            email=request.user.email or f"{request.user.username}@example.com"
        )
    clients = Client.objects.all()
    invoices = Invoice.objects.all()
    occupied_spots = ParkingSpot.objects.filter(is_occupied=True).select_related('car').prefetch_related('car__clients')
    clients_with_debt = Client.objects.filter(cars__invoice__debt__gt=0).annotate(total_debt=Sum('cars__invoice__debt')).distinct()

    return render(request, 'parking/employee_dashboard.html', {
        'employee': employee,
        'clients': clients,
        'invoices': invoices,
        'occupied_spots': occupied_spots,
        'clients_with_debt': clients_with_debt,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

def get_new_clients_data():
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    # Генерируем список всех дней в диапазоне
    all_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    
    # Используем TruncDate вместо extra
    clients_per_day = Client.objects.filter(
        date_added__date__gte=start_date,
        date_added__date__lte=end_date
    ).annotate(date=TruncDate('date_added')).values('date').annotate(count=Count('id')).order_by('date')

    # Преобразуем данные в словарь для удобства
    clients_dict = {item['date']: item['count'] for item in clients_per_day}
    # Заполняем значения для всех дней, даже если данных нет (0 клиентов)
    labels = [d.strftime('%Y-%m-%d') for d in all_dates]
    values = [clients_dict.get(d, 0) for d in all_dates]
    
    print(f"Debug - Labels: {labels}")  # Отладочная информация
    print(f"Debug - Values: {values}")  # Отладочная информация
    return labels, values

def generate_chart(labels, values):
    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color='skyblue')
    plt.title('Новые клиенты за последние 30 дней (по дням)')
    plt.xlabel('Дата')
    plt.ylabel('Количество новых клиентов')
    plt.xticks(rotation=90)  # Поворот меток для лучшей читаемости
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return image_base64

# Страница админа (доступна только админу)
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('home')

    clients = Client.objects.all()
    cars = Car.objects.all()
    parking_spots = ParkingSpot.objects.all()
    occupied_spots = ParkingSpot.objects.filter(is_occupied=True).select_related('car').prefetch_related('car__clients')
    clients_with_debt = Client.objects.filter(cars__invoice__debt__gt=0).annotate(total_debt=Sum('cars__invoice__debt')).distinct()
    incoms = Income.objects.all()
    labels, values = get_new_clients_data()
    chart_image = generate_chart(labels, values)

    return render(request, 'parking/admin_dashboard.html', {
        'clients': clients,
        'cars': cars,
        'incoms':incoms,
        'parking_spots': parking_spots,
        'occupied_spots': occupied_spots,
        'clients_with_debt': clients_with_debt,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
        'chart_image': chart_image,
    })

# CRUD для Client
class ClientListView(ListView):
    model = Client
    template_name = 'parking/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        user = self.request.user
        if is_admin(user):
            return Client.objects.all()
        elif is_client(user):
            return Client.objects.filter(user=user)
        return Client.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class ClientCreateView(CreateView):
    model = Client
    fields = ['user', 'name', 'email', 'age', 'timezone']
    template_name = 'parking/client_form.html'
    success_url = reverse_lazy('client_list')

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class ClientDeleteView(DeleteView):
    model = Client
    template_name = 'parking/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

# CRUD для Car (админ и клиент)
class CarCreateView(CreateView):
    model = Car
    fields = ['license_plate', 'brand', 'model', 'clients']
    template_name = 'parking/car_form.html'
    success_url = reverse_lazy('client_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (is_admin(request.user) or is_client(request.user)):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        current_user = self.request.user
        if is_client(self.request.user):
            current_client = Client.objects.get(user=current_user)
            form.fields['clients'].queryset = Client.objects.all()
            form.initial['clients'] = [current_client.id]
            form.fields['clients'].widget.attrs.update({'multiple': 'multiple'})
        else:
            form.fields['clients'].queryset = Client.objects.all()
            form.fields['clients'].widget.attrs.update({'multiple': 'multiple'})
        return form

    def form_valid(self, form):
        try:
            car = form.save(commit=False)
            car.save()
            selected_clients = form.cleaned_data['clients']
            if is_client(self.request.user):
                current_client = Client.objects.get(user=self.request.user)
                if current_client not in selected_clients:
                    selected_clients = list(selected_clients) + [current_client]
            car.clients.set(selected_clients)
            return super().form_valid(form)
        except Exception as e:
            form.add_error(None, f"Ошибка при создании автомобиля: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class CarListView(ListView):
    model = Car
    template_name = 'parking/car_list.html'
    context_object_name = 'cars'

    def get_queryset(self):
        user = self.request.user
        if is_admin(user):
            return Car.objects.all()
        elif is_client(user):
            client = Client.objects.get(user=user)
            return Car.objects.filter(clients=client)
        return Car.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class CarUpdateView(UpdateView):
    model = Car
    fields = ['license_plate', 'brand', 'model', 'clients']
    template_name = 'parking/car_form.html'
    success_url = reverse_lazy('client_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (is_admin(request.user) or is_client(request.user)):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if is_admin(user) or (is_client(user) and obj.clients.filter(user=user).exists()):
            return obj
        raise Http404("У вас нет доступа к редактированию этого автомобиля")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        current_user = self.request.user
        if is_client(self.request.user):
            current_client = Client.objects.get(user=current_user)
            form.fields['clients'].queryset = Client.objects.all()
            form.initial['clients'] = list(self.object.clients.values_list('id', flat=True))
            form.fields['clients'].widget.attrs.update({'multiple': 'multiple'})
        else:
            form.fields['clients'].queryset = Client.objects.all()
            form.fields['clients'].widget.attrs.update({'multiple': 'multiple'})
        return form

    def form_valid(self, form):
        try:
            car = form.save(commit=False)
            selected_clients = form.cleaned_data['clients']
            if is_client(self.request.user):
                current_client = Client.objects.get(user=self.request.user)
                if current_client not in selected_clients:
                    selected_clients = list(selected_clients) + [current_client]
            car.clients.set(selected_clients)
            car.save()
            return super().form_valid(form)
        except Exception as e:
            form.add_error(None, f"Ошибка при обновлении автомобиля: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class CarDeleteView(DeleteView):
    model = Car
    template_name = 'parking/car_confirm_delete.html'
    success_url = reverse_lazy('client_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (is_admin(request.user) or is_client(request.user)):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        if is_admin(user) or (is_client(user) and obj in Client.objects.get(user=user).cars.all()):
            return obj
        raise Http404("У вас нет доступа к удалению этого автомобиля")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        ParkingSpot.objects.filter(car=obj, is_occupied=True).update(car=None, is_occupied=False)
        return super().delete(request, *args, **kwargs)

# CRUD для ParkingSpot (только админ)
class ParkingSpotCreateView(CreateView):
    model = ParkingSpot
    fields = ['number', 'price', 'is_occupied']
    template_name = 'parking/parkingspot_form.html'
    success_url = reverse_lazy('parkingspot_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            if form.instance.is_occupied and not form.instance.car:
                form.instance.is_occupied = False
            return super().form_valid(form)
        except Exception as e:
            form.add_error(None, f"Ошибка при создании парковочного места: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class ParkingSpotListView(ListView):
    model = ParkingSpot
    template_name = 'parking/parkingspot_list.html'
    context_object_name = 'parking_spots'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class ParkingSpotUpdateView(UpdateView):
    model = ParkingSpot
    fields = ['number', 'price', 'is_occupied']
    template_name = 'parking/parkingspot_form.html'
    success_url = reverse_lazy('parkingspot_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            if form.instance.is_occupied and not form.instance.car:
                form.instance.is_occupied = False
            if not form.instance.is_occupied and form.instance.car:
                form.instance.car = None
            return super().form_valid(form)
        except Exception as e:
            form.add_error(None, f"Ошибка при обновлении парковочного места: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

class ParkingSpotDeleteView(DeleteView):
    model = ParkingSpot
    template_name = 'parking/parkingspot_confirm_delete.html'
    success_url = reverse_lazy('parkingspot_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = is_admin(self.request.user)
        context['is_client'] = is_client(self.request.user)
        context['is_employee'] = is_employee(self.request.user)
        return context

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        Invoice.objects.filter(parking_spot=obj).delete()
        return super().delete(request, *args, **kwargs)

# Занятие парковочного места клиентом
@login_required
@user_passes_test(is_client)
def occupy_spot(request, spot_id):
    if not is_client(request.user):
        return redirect('home')

    spot = get_object_or_404(ParkingSpot, id=spot_id)
    client = Client.objects.get(user=request.user)
    if spot.is_occupied:
        return render(request, 'parking/error.html', {
            'message': 'Место уже занято',
            'is_admin': is_admin(request.user),
            'is_client': is_client(request.user),
            'is_employee': is_employee(request.user),
        })
    if request.method == 'POST':
        car_id = request.POST.get('car')
        car = Car.objects.get(id=car_id)
        if client in car.clients.all():
            if ParkingSpot.objects.filter(car=car, is_occupied=True).exists():
                return render(request, 'parking/error.html', {
                    'message': 'Этот автомобиль уже занимает парковочное место',
                    'is_admin': is_admin(request.user),
                    'is_client': is_client(request.user),
                    'is_employee': is_employee(request.user),
                })
            ParkingSpot.objects.filter(car=car, is_occupied=True).update(car=None, is_occupied=False)
            spot.is_occupied = True
            spot.car = car
            spot.save()
            from django.utils.crypto import get_random_string
            invoice_code = get_random_string(length=8)
            Invoice.objects.create(
                code=invoice_code,
                car=car,
                parking_spot=spot,
                spot_price=spot.price,
                issue_date=timezone.now().date(),
                payment_date=None,
                debt=0
            )
            return redirect('client_dashboard')
    return render(request, 'parking/occupy_spot.html', {
        'spot': spot,
        'cars': client.cars.all(),
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Освобождение парковочного места клиентом
@login_required
@user_passes_test(is_client)
def free_parking_spot(request, spot_id):
    if not is_client(request.user):
        return redirect('home')

    spot = get_object_or_404(ParkingSpot, id=spot_id)
    client = Client.objects.get(user=request.user)
    if not spot.is_occupied or spot.car not in client.cars.all():
        return render(request, 'parking/error.html', {
            'message': 'Это место не занято вашим автомобилем',
            'is_admin': is_admin(request.user),
            'is_client': is_client(request.user),
            'is_employee': is_employee(request.user),
        })
    if request.method == 'POST':
        spot.is_occupied = False
        spot.car = None
        spot.save()
        invoice = Invoice.objects.filter(parking_spot=spot, payment_date__isnull=True).first()
        if invoice:
            issue_datetime = timezone.make_aware(datetime.combine(invoice.issue_date, time.min), timezone.get_current_timezone())
            now = timezone.now()
            days_passed = (now - issue_datetime).days
            if days_passed > 30:
                invoice.debt = invoice.spot_price
                invoice.save()
            else:
                invoice.delete()
        return redirect('client_dashboard')
    return render(request, 'parking/free_spot_confirm.html', {
        'spot': spot,
        'car': spot.car,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Изменение цены парковочного места (админ)
@login_required
@user_passes_test(is_admin)
def update_spot_price(request, spot_id):
    if not is_admin(request.user):
        return redirect('home')

    spot = get_object_or_404(ParkingSpot, id=spot_id)
    if request.method == 'POST':
        new_price = request.POST.get('price')
        spot.price = new_price
        spot.save()
        return redirect('admin_dashboard')
    return render(request, 'parking/update_spot_price.html', {
        'spot': spot,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Клиент с наибольшим долгом (админ)
@login_required
@user_passes_test(is_admin)
def biggest_debtor(request):
    if not is_admin(request.user):
        return redirect('home')

    clients = Client.objects.all()
    debtor = None
    max_debt = float('-inf')
    last_payment = None

    for client in clients:
        invoices = Invoice.objects.filter(car__in=client.cars.all())
        total_debt = sum(invoice.debt for invoice in invoices)
        if total_debt > max_debt:
            max_debt = total_debt
            debtor = client
            last_payment = invoices.filter(payment_date__isnull=False).order_by('-payment_date').first()

    return render(request, 'parking/biggest_debtor.html', {
        'debtor': debtor,
        'max_debt': max_debt,
        'last_payment': last_payment.payment_date if last_payment else None,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Автомобили с несколькими владельцами (админ)
@login_required
@user_passes_test(is_admin)
def cars_with_multiple_owners(request):
    if not is_admin(request.user):
        return redirect('home')

    cars = Car.objects.annotate(num_owners=Count('clients')).filter(num_owners__gt=1)
    car_owners = [(car, car.clients.all()) for car in cars]
    return render(request, 'parking/cars_with_multiple_owners.html', {
        'car_owners': car_owners,
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Автомобиль с наименьшим долгом за период (админ)
@login_required
@user_passes_test(is_admin)
def car_with_min_debt(request):
    if not is_admin(request.user):
        return redirect('home')

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        cars = Car.objects.all()
        min_debt = float('inf')
        min_debt_car = None

        for car in cars:
            invoices = Invoice.objects.filter(car=car, issue_date__range=[start_date, end_date])
            total_debt = sum(invoice.debt for invoice in invoices)
            if total_debt < min_debt:
                min_debt = total_debt
                min_debt_car = car

        return render(request, 'parking/car_with_min_debt.html', {
            'car': min_debt_car,
            'min_debt': min_debt,
            'start_date': start_date,
            'end_date': end_date,
            'is_admin': is_admin(request.user),
            'is_client': is_client(request.user),
            'is_employee': is_employee(request.user),
        })
    return render(request, 'parking/car_with_min_debt_form.html', {
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Сумма долгов за период (админ)
@login_required
@user_passes_test(is_admin)
def total_debt(request):
    if not is_admin(request.user):
        return redirect('home')

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        invoices = Invoice.objects.filter(issue_date__range=[start_date, end_date])
        total_debt = sum(invoice.debt for invoice in invoices)

        return render(request, 'parking/total_debt.html', {
            'total_debt': total_debt,
            'start_date': start_date,
            'end_date': end_date,
            'is_admin': is_admin(request.user),
            'is_client': is_client(request.user),
            'is_employee': is_employee(request.user),
        })
    return render(request, 'parking/total_debt_form.html', {
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })

# Автомобили по марке (админ)
@login_required
@user_passes_test(is_admin)
def cars_by_brand(request):
    if not is_admin(request.user):
        return redirect('home')

    if request.method == 'POST':
        brand = request.POST.get('brand')
        cars = Car.objects.filter(brand__iexact=brand)
        car_owners = [(car, car.clients.all()) for car in cars]
        return render(request, 'parking/cars_by_brand.html', {
            'brand': brand,
            'car_owners': car_owners,
            'is_admin': is_admin(request.user),
            'is_client': is_client(request.user),
            'is_employee': is_employee(request.user),
        })
    return render(request, 'parking/cars_by_brand_form.html', {
        'is_admin': is_admin(request.user),
        'is_client': is_client(request.user),
        'is_employee': is_employee(request.user),
    })