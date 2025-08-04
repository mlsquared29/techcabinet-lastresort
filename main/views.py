from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import PSAGroup, PSAEntry, AIResponse, Competition
from .forms import PSAEntryForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('main:dashboard'))
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Account '{form.cleaned_data.get('username')}' created successfully.")
            return HttpResponseRedirect(reverse('main:login'))
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('main:dashboard'))
    
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return HttpResponseRedirect(reverse('main:dashboard'))
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form})

@login_required(login_url='main:login')
def dashboard(request):
    competitions = Competition.objects.filter(is_active=True).order_by('-pub_date')
    competitions_to_update = Competition.objects.all()
    for competition in competitions_to_update:
        competition.save()

    your_competitions = request.user.competitions.all().order_by('-is_active', '-pub_date')
    active_competitions = Competition.objects.filter(is_active=True).exclude(user=request.user).order_by('-pub_date')
    past_competitions = Competition.objects.filter(is_active=False).exclude(user=request.user).order_by('-end_date')
    
    return render(request, 'main/dashboard.html', {
        'your_competitions': your_competitions,
        'active_competitions': active_competitions,
        'past_competitions': past_competitions
    })

@login_required(login_url='main:login')
def competition(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    return render(request, 'main/competition.html', {'competition': competition})

@login_required(login_url='main:login')
def submit(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if not competition.is_active:
        return render(request, 'main/access_denied.html', {
            'error_message': 'This competition is no longer active.'
        })
    
    if request.user not in competition.user.all():
        return render(request, 'main/access_denied.html', {
            'error_message': 'You are not registered for this competition.'
        })
    
    if request.method == 'POST':
        form = PSAEntryForm(request.POST, num_questions=competition.num_questions)
        if form.is_valid():
            group = PSAGroup.objects.create(name=f"{request.user.username}", competition=competition, user=request.user)
            for i in range(competition.num_questions):
                psa_entry = PSAEntry.objects.create(group=group, problem=form.cleaned_data[f'question_{i}'], solution=form.cleaned_data[f'solution_{i}'], answer=form.cleaned_data[f'answer_{i}'])
                
            from .tasks import generate_ai_responses
            generate_ai_responses.delay_on_commit(group.id)
            
            return HttpResponseRedirect(reverse('main:output', args=(group.id, competition.id,)))
    else:
        form = PSAEntryForm(num_questions=competition.num_questions)
    return render(request, 'main/submit.html', {
        'competition': competition,
        'form': form,
        'num_questions': competition.num_questions,
        'question_range': range(competition.num_questions)
    })

@login_required(login_url='main:login')
def output(request, psa_group_id, competition_id):
    psa_group = get_object_or_404(PSAGroup, pk=psa_group_id)
    competition = get_object_or_404(Competition, pk=competition_id)
    psa_entries = psa_group.psaentry_set.all().order_by('-pub_date')
    ai_responses = AIResponse.objects.filter(psa_entry__group=psa_group).order_by('-pub_date')
    return render(request, 'main/output.html', {
        'psa_group': psa_group,
        'competition': competition,
        'psa_entries': psa_entries,
        'ai_responses': ai_responses
    })

@login_required(login_url='main:login')
def check_outputs(request, psa_group_id):
    """HTMX endpoint to check for outputs"""
    psa_group = get_object_or_404(PSAGroup, pk=psa_group_id)
    psa_entries = psa_group.psaentry_set.all()
    ai_responses = AIResponse.objects.filter(psa_entry__group=psa_group).order_by('-pub_date')
    
    if ai_responses.count() >= psa_entries.count():
        correct = 0
        for ai_response in ai_responses:
            if ai_response.psa_entry.answer == ai_response.ai_answer:
                correct += 1
        psa_group.score = 100-correct*100/psa_entries.count()
        psa_group.save()
        return render(request, 'main/outputs_partial.html', {
            'psa_group': psa_group,
            'psa_entries': psa_entries,
            'ai_responses': ai_responses
        })
    else:
        return render(request, 'main/loading_partial.html', {
            'psa_group': psa_group,
            'psa_entries': psa_entries,
            'ai_responses': ai_responses
        })

@login_required(login_url='main:login')
def leaderboard(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    all_groups = PSAGroup.objects.filter(competition=competition).select_related('user').order_by('user__username', '-score')
    
    user_best_scores = {}
    for group in all_groups:
        username = group.user.username
        if username not in user_best_scores:
            user_best_scores[username] = {
                'username': username,
                'best_score': group.score,
                'best_submission_date': group.pub_date,
                'user_id': group.user.id
            }
    
    psa_groups = sorted(user_best_scores.values(), key=lambda x: x['best_score'], reverse=True)
    
    if psa_groups:
        total_score = sum(group['best_score'] for group in psa_groups)
        average_score = total_score / len(psa_groups)
    else:
        average_score = 0
    
    return render(request, 'main/leaderboard.html', {
        'competition': competition,
        'psa_groups': psa_groups,
        'average_score': average_score
    })

@login_required(login_url='main:login')
def register_competition(request, competition_id):
    if request.method == 'POST':
        competition = get_object_or_404(Competition, pk=competition_id)
        
        # Check if competition is active
        if not competition.is_active:
            messages.error(request, 'Cannot register for an inactive competition.')
            return HttpResponseRedirect(reverse('main:competition', args=(competition.id,)))
        
        # Check if user is already registered
        if request.user in competition.user.all():
            messages.info(request, 'You are already registered for this competition.')
            return HttpResponseRedirect(reverse('main:competition', args=(competition.id,)))
        
        # Register the user for the competition
        competition.user.add(request.user)
        messages.success(request, f'Successfully registered for "{competition.name}"!')
        
        return HttpResponseRedirect(reverse('main:competition', args=(competition.id,)))
    
    # If not POST, redirect to competition page
    return HttpResponseRedirect(reverse('main:competition', args=(competition_id,)))

def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return HttpResponseRedirect(reverse('main:login'))

def landing(request):
    return render(request, 'main/landing.html')



