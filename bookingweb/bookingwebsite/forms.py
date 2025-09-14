from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

BASE = "w-full rounded-md border-2 border-slate-500 focus:border-slate-600 focus:ring-2 focus:ring-slate-300"


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": BASE})
        self.fields["password1"].widget.attrs.update({"class": BASE + " pr-10", "id": "pw1"})
        self.fields["password2"].widget.attrs.update({"class": BASE + " pr-10", "id": "pw2"})

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": BASE})
        self.fields["password"].widget.attrs.update({"class": BASE + " pr-10", "id": "login-password"})
