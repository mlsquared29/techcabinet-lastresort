from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import PSAGroup, PSAEntry, AIResponse
from .forms import PSAEntryForm, NUM_QUESTIONS

def process_query(request):
    if request.method == 'POST':
        form = PSAEntryForm(request.POST)
        if form.is_valid():
            group = PSAGroup.objects.create(name=f"Group {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            for i in range(NUM_QUESTIONS):
                psa_entry = PSAEntry.objects.create(group=group, problem=form.cleaned_data[f'question_{i}'], solution=form.cleaned_data[f'solution_{i}'], answer=form.cleaned_data[f'answer_{i}'])
                
            from .tasks import generate_ai_responses
            generate_ai_responses.delay_on_commit(group.id)
            
            return HttpResponseRedirect(reverse('main:output', args=(group.id,)))
    else:
        form = PSAEntryForm()
    return render(request, 'main/process_query.html', {
        'form': form,
        'num_questions': NUM_QUESTIONS,
        'question_range': range(NUM_QUESTIONS)
    })

def output(request, psa_group_id):
    psa_group = get_object_or_404(PSAGroup, pk=psa_group_id)
    psa_entries = psa_group.psaentry_set.all().order_by('-pub_date')
    ai_responses = AIResponse.objects.filter(psa_entry__group=psa_group).order_by('-pub_date')
    return render(request, 'main/output.html', {
        'psa_group': psa_group,
        'psa_entries': psa_entries,
        'ai_responses': ai_responses
    })

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
    
def leaderboard(request):
    psa_groups = PSAGroup.objects.all().order_by('-score')
    
    # Calculate average score
    if psa_groups.exists():
        total_score = sum(group.score for group in psa_groups)
        average_score = total_score / psa_groups.count()
    else:
        average_score = 0
    
    return render(request, 'main/leaderboard.html', {
        'psa_groups': psa_groups,
        'average_score': average_score
    })