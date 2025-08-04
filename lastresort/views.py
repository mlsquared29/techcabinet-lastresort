from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from .models import PSAGroup, PSAEntry, AIResponse, Competition
from .forms import PSAEntryForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from celery import chain

def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lastresort:dashboard'))
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Account '{form.cleaned_data.get('username')}' created successfully.")
            return HttpResponseRedirect(reverse('lastresort:login'))
    else:
        form = UserCreationForm()
    return render(request, 'lastresort/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('lastresort:dashboard'))
    
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return HttpResponseRedirect(reverse('lastresort:dashboard'))
    else:
        form = AuthenticationForm()
    return render(request, 'lastresort/login.html', {'form': form})

@login_required(login_url='lastresort:login')
def dashboard(request):
    competitions = Competition.objects.filter(is_active=True).order_by('-pub_date')
    competitions_to_update = Competition.objects.all()
    for competition in competitions_to_update:
        competition.save()

    your_competitions = request.user.competitions.all().order_by('-is_active', '-pub_date')
    active_competitions = Competition.objects.filter(is_active=True).exclude(user=request.user).order_by('-pub_date')
    past_competitions = Competition.objects.filter(is_active=False).exclude(user=request.user).order_by('-end_date')
    
    return render(request, 'lastresort/dashboard.html', {
        'your_competitions': your_competitions,
        'active_competitions': active_competitions,
        'past_competitions': past_competitions
    })

@login_required(login_url='lastresort:login')
def competition(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Get user's submissions for this competition
    user_submissions = PSAGroup.objects.filter(
        competition=competition,
        user=request.user
    ).order_by('-pub_date')
    
    return render(request, 'lastresort/competition.html', {
        'competition': competition,
        'user_submissions': user_submissions
    })

@login_required(login_url='lastresort:login')
def submit(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if not competition.is_active:
        return render(request, 'lastresort/access_denied.html', {
            'error_message': 'This competition is no longer active.'
        })
    
    if request.user not in competition.user.all():
        return render(request, 'lastresort/access_denied.html', {
            'error_message': 'You are not registered for this competition.'
        })
    
    if request.method == 'POST':
        form = PSAEntryForm(request.POST, num_questions=competition.num_questions)
        if form.is_valid():
            group = PSAGroup.objects.create(
                name=f"{request.user.username}", 
                competition=competition, 
                user=request.user,
                status='pending'
            )
            for i in range(competition.num_questions):
                psa_entry = PSAEntry.objects.create(group=group, problem=form.cleaned_data[f'question_{i}'], solution=form.cleaned_data[f'solution_{i}'], answer=form.cleaned_data[f'answer_{i}'])
            
            messages.success(request, 'Your submission has been submitted successfully and is pending admin review.')
            return HttpResponseRedirect(reverse('lastresort:competition', args=(competition.id,)))
    else:
        form = PSAEntryForm(num_questions=competition.num_questions)
    return render(request, 'lastresort/submit.html', {
        'competition': competition,
        'form': form,
        'num_questions': competition.num_questions,
        'question_range': range(competition.num_questions)
    })

@login_required(login_url='lastresort:login')
def output(request, psa_group_id, competition_id):
    psa_group = get_object_or_404(PSAGroup, pk=psa_group_id)
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if psa_group.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'lastresort/access_denied.html', {
            'error_message': 'You can only view your own submissions.'
        })
    
    if psa_group.status not in ['accepted', 'completed']:
        return render(request, 'lastresort/access_denied.html', {
            'error_message': 'This submission is pending review or has been rejected.'
        })
    
    psa_entries = psa_group.psaentry_set.all().order_by('-pub_date')
    ai_responses = AIResponse.objects.filter(psa_entry__group=psa_group).order_by('-pub_date')
    return render(request, 'lastresort/output.html', {
        'psa_group': psa_group,
        'competition': competition,
        'psa_entries': psa_entries,
        'ai_responses': ai_responses
    })

@login_required(login_url='lastresort:login')
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
        return render(request, 'lastresort/outputs_partial.html', {
            'psa_group': psa_group,
            'psa_entries': psa_entries,
            'ai_responses': ai_responses
        })
    else:
        return render(request, 'lastresort/loading_partial.html', {
            'psa_group': psa_group,
            'psa_entries': psa_entries,
            'ai_responses': ai_responses
        })

@login_required(login_url='lastresort:login')
def leaderboard(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    all_groups = PSAGroup.objects.filter(
        competition=competition, 
        status__in=['accepted', 'completed']
    ).select_related('user').order_by('user__username', '-score')
    
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
    
    return render(request, 'lastresort/leaderboard.html', {
        'competition': competition,
        'psa_groups': psa_groups,
        'average_score': average_score
    })

@login_required(login_url='lastresort:login')
def register_competition(request, competition_id):
    if request.method == 'POST':
        competition = get_object_or_404(Competition, pk=competition_id)
        
        # Check if competition is active
        if not competition.is_active:
            messages.error(request, 'Cannot register for an inactive competition.')
            return HttpResponseRedirect(reverse('lastresort:competition', args=(competition.id,)))
        
        # Check if user is already registered
        if request.user in competition.user.all():
            messages.info(request, 'You are already registered for this competition.')
            return HttpResponseRedirect(reverse('lastresort:competition', args=(competition.id,)))
        
        # Register the user for the competition
        competition.user.add(request.user)
        messages.success(request, f'Successfully registered for "{competition.name}"!')
        
        return HttpResponseRedirect(reverse('lastresort:competition', args=(competition.id,)))
    
    # If not POST, redirect to competition page
    return HttpResponseRedirect(reverse('lastresort:competition', args=(competition_id,)))

def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return HttpResponseRedirect(reverse('lastresort:login'))

def landing(request):
    return render(request, 'lastresort/landing.html')

@login_required(login_url='lastresort:login')
def download_submission(request, psa_group_id):
    """Download submission data as a text file"""
    psa_group = get_object_or_404(PSAGroup, pk=psa_group_id)
    
    # Ensure user can only download their own submissions
    if psa_group.user != request.user:
        return render(request, 'lastresort/access_denied.html', {
            'error_message': 'You can only download your own submissions.'
        })
    
    # Get all PSA entries for this group
    psa_entries = PSAEntry.objects.filter(group=psa_group).order_by('pub_date')
    
    # Generate the text content
    content = f"Submission Details\n"
    content += f"=" * 50 + "\n\n"
    content += f"Competition: {psa_group.competition.name}\n"
    content += f"Submitted by: {psa_group.user.username}\n"
    content += f"Submission Date: {psa_group.pub_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"Status: {psa_group.status}\n"
    content += f"Score: {psa_group.score}%\n"
    if psa_group.reason:
        content += f"Reason: {psa_group.reason}\n"
    content += f"\n"
    
    content += f"Questions and Solutions\n"
    content += f"=" * 50 + "\n\n"
    
    for i, entry in enumerate(psa_entries, 1):
        content += f"Question {i}:\n"
        content += f"Problem: {entry.problem}\n"
        content += f"Solution: {entry.solution}\n"
        content += f"Answer: {entry.answer}\n"
        content += f"Submitted: {entry.pub_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"\n"
    
    # Create the response
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="submission_{psa_group.id}_{psa_group.user.username}.txt"'
    
    return response

@login_required(login_url='lastresort:login')
def admin_review(request, competition_id):
    """Admin view to review all submissions for a competition"""
    competition = get_object_or_404(Competition, pk=competition_id)
    
    if not request.user.is_staff and not request.user.is_superuser:
        return render(request, 'lastresort/access_denied.html', {
            'error_message': 'You do not have permission to access this page.'
        })
    
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        
        if submission_id and action:
            submission = get_object_or_404(PSAGroup, pk=submission_id, competition=competition)
            
            if action == 'accept':
                submission.status = 'accepted'
                submission.reason = reason
                submission.save()
                
                from .tasks import generate_ai_responses, mark_submission_completed
                from django.db import transaction
                chain = generate_ai_responses.s(submission.id) | mark_submission_completed.s(submission.id)
                transaction.on_commit(lambda: chain.delay())
                
                messages.success(request, f'Submission #{submission.id} has been accepted.')
                
            elif action == 'reject':
                submission.status = 'rejected'
                submission.reason = reason
                submission.save()
                
                messages.success(request, f'Submission #{submission.id} has been rejected.')
            
            return HttpResponseRedirect(reverse('lastresort:admin_review', args=(competition.id,)))
    
    submissions = PSAGroup.objects.filter(
        competition=competition,
        status__in=['pending']
    ).select_related('user').order_by('-pub_date')
    
    return render(request, 'lastresort/admin_review.html', {
        'competition': competition,
        'submissions': submissions
    })



