from django.urls import path
from .views import RegisterView, ProfileView, ProfileEditView

app_name = "users"


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
]
