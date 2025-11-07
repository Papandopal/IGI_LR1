from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from parking.models import Client
import datetime

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Введите ваш email.')
    age = forms.DateField()
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def is_valid(self):
        try:
            a = datetime.date.fromisoformat(self.data['age'])
            b = datetime.date.today()
            
            if (b - a).days < 365.25 * 18:
                print("asdsasd", (a - b).days)
                return False
        except Exception as e:
            print(e)
            return False
        
        return super().is_valid()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        
        # raise Exception("failed")
        # if 
        
        if commit:
            user.save()
            # Добавляем пользователя в группу Client
            client_group = Group.objects.get(name='Client')
            user.groups.add(client_group)
            # Создаём запись Client
            Client.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                age=self.cleaned_data['age']
            )
        return user