import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, F
from .models import Quote, ViewHistory
from .forms import QuoteForm

def random_quote(request):
    quotes = Quote.objects.all()
    selected = None
    if quotes.exists():
        # Получаем ключ сессии
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # Для авторизованных пользователей
        if request.user.is_authenticated:
            viewed_quotes = ViewHistory.objects.filter(user=request.user).values_list('quote__pk', flat=True)
            available_quotes = quotes.exclude(pk__in=viewed_quotes)
        else:
            # Для гостей используем сессию
            viewed_quotes = ViewHistory.objects.filter(session_key=session_key).values_list('quote__pk', flat=True)
            available_quotes = quotes.exclude(pk__in=viewed_quotes)

        if available_quotes.exists():
            # Фильтруем цитаты с ненулевым весом
            valid_quotes = available_quotes.filter(weight__gt=0)
            if valid_quotes.exists():
                selected = random.choices(valid_quotes, weights=[q.weight for q in valid_quotes], k=1)[0]
            else:
                # Если все веса 0, выбираем случайную цитату без весов
                selected = random.choice(list(available_quotes))
            # Увеличиваем просмотры и сохраняем историю
            if request.user.is_authenticated:
                if not ViewHistory.objects.filter(user=request.user, quote=selected).exists():
                    Quote.objects.filter(pk=selected.pk).update(views=F('views') + 1)
                    ViewHistory.objects.create(user=request.user, quote=selected)
            else:
                if not ViewHistory.objects.filter(session_key=session_key, quote=selected).exists():
                    Quote.objects.filter(pk=selected.pk).update(views=F('views') + 1)
                    ViewHistory.objects.create(session_key=session_key, quote=selected)
            selected.refresh_from_db()
        else:
            # Если все цитаты просмотрены
            valid_quotes = quotes.filter(weight__gt=0)
            if valid_quotes.exists():
                selected = random.choices(valid_quotes, weights=[q.weight for q in valid_quotes], k=1)[0]
            else:
                selected = random.choice(list(quotes))

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string('quote_partial.html', {'quote': selected, 'user': request.user}, request=request)
            return JsonResponse({'html': html})
        
    return render(request, 'random_quote.html', {'quote': selected, 'user': request.user})
@login_required
def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Цитата успешно добавлена!')
                return redirect('random_quote')
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Ошибка в форме. Проверьте данные.')
    else:
        form = QuoteForm()
    return render(request, 'add_quote.html', {'form': form})

@login_required
def like_quote(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    if request.method == 'POST':
        if request.user not in quote.likes.all() and request.user not in quote.dislikes.all():
            quote.likes.add(request.user)
            messages.success(request, 'Лайк добавлен!')
        else:
            messages.warning(request, 'Вы уже проголосовали за эту цитату.')
        return JsonResponse({'likes': quote.likes.count(), 'dislikes': quote.dislikes.count()})
    return redirect('random_quote')

@login_required
def dislike_quote(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    if request.method == 'POST':
        if request.user not in quote.likes.all() and request.user not in quote.dislikes.all():
            quote.dislikes.add(request.user)
            messages.success(request, 'Дизлайк добавлен!')
        else:
            messages.warning(request, 'Вы уже проголосовали за эту цитату.')
        return JsonResponse({'likes': quote.likes.count(), 'dislikes': quote.dislikes.count()})
    return redirect('random_quote')

def dashboard(request):
    top_quotes = Quote.objects.annotate(
        net_likes=Count('likes') - Count('dislikes')
    ).order_by('-net_likes')[:10]
    
    source_filter = request.GET.get('source')
    search = request.GET.get('search')
    quotes = Quote.objects.all()
    if source_filter:
        quotes = quotes.filter(source__icontains=source_filter)
    if search:
        quotes = quotes.filter(Q(text__icontains=search) | Q(source__icontains=search))
    
    return render(request, 'dashboard.html', {'top_quotes': top_quotes, 'quotes': quotes})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли!')
            return redirect('random_quote')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Вы вышли из аккаунта')
    return redirect('random_quote')

def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        if len(password) < 8:
            messages.error(request, 'Пароль должен быть не короче 8 символов')
        elif password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Имя пользователя уже занято')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email уже используется')
        else:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                login(request, user)
                messages.success(request, 'Регистрация успешна! Вы вошли в аккаунт.')
                return redirect('random_quote')
            except Exception as e:
                messages.error(request, f'Ошибка регистрации: {str(e)}')
    return render(request, 'register.html')