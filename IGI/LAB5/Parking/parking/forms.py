from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from parking.models import Client

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Введите ваш email.')
    age = forms.IntegerField(
        label='Возраст',
        min_value=18,
        max_value=120,
        help_text='Возраст должен быть от 18 до 120 лет.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
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