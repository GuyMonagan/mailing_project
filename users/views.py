from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from .models import User


class RegisterView(CreateView):
    """
    Страница регистрации нового пользователя.

    Использует кастомную форму и автоматически логинит пользователя после успешной регистрации.
    """
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("mailing:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # логиним нового пользователя сразу
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Профиль текущего пользователя (только просмотр).

    Доступен только авторизованным пользователям.
    """
    template_name = "users/profile.html"


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Редактирование профиля пользователя (аватар, телефон, страна).

    Загружает текущего пользователя как объект редактирования.
    """
    model = User
    fields = ['avatar', 'phone', 'country']
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self):
        return self.request.user
