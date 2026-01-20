from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """
    Форма аутентификации по email вместо username.

    Использует поле email как идентификатор пользователя.
    """
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)


class CustomUserCreationForm(UserCreationForm):
    """
    Кастомная форма регистрации пользователя.

    Поля: email, телефон, страна, аватар и пароль.
    Устанавливает email как username.
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "phone", "country", "avatar", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]  # fallback на случай, если username нужен
        if commit:
            user.save()
        return user
