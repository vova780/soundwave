from django import forms


class UploadTrackForm(forms.Form):
    title = forms.CharField(
        max_length=200, label='Название трека',
        widget=forms.TextInput(attrs={'placeholder': 'Название трека', 'class': 'form-input'})
    )
    artist = forms.CharField(
        max_length=200, label='Исполнитель',
        widget=forms.TextInput(attrs={'placeholder': 'Имя исполнителя', 'class': 'form-input'})
    )
    audio_file = forms.FileField(
        label='Аудио файл',
        widget=forms.FileInput(attrs={'accept': 'audio/*', 'class': 'form-file'})
    )
    cover_image = forms.ImageField(
        label='Обложка трека', required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-file'})
    )


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=50, label='Имя пользователя',
        widget=forms.TextInput(attrs={'placeholder': 'Ваш ник', 'class': 'form-input'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль', 'class': 'form-input'})
    )


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=50, label='Имя пользователя',
        widget=forms.TextInput(attrs={'placeholder': 'Ваш ник', 'class': 'form-input'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль', 'class': 'form-input'})
    )


class CreatePlaylistForm(forms.Form):
    name = forms.CharField(
        max_length=100, label='Название плейлиста',
        widget=forms.TextInput(attrs={'placeholder': 'Название плейлиста', 'class': 'form-input'})
    )
