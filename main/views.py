from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Query, Output
from .forms import QueryForm

def process_query(request):
    if request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            query_text = form.cleaned_data['query']
            query_amount = form.cleaned_data['amount']
            query = Query.objects.create(query=query_text, amount=query_amount)

            from .tasks import generate_outputs_for_query
            generate_outputs_for_query.delay_on_commit(query.id)
            
            return HttpResponseRedirect(reverse('main:output', args=(query.id,)))
    else:
        form = QueryForm()
    return render(request, 'main/process_query.html', {'form': form})

def output(request, query_id):
    query = get_object_or_404(Query, pk=query_id)
    outputs = query.output_set.all().order_by('-votes', '-pub_date')
    return render(request, 'main/output.html', {
        'query': query,
        'outputs': outputs
    })

def check_outputs(request, query_id):
    """HTMX endpoint to check for outputs"""
    query = get_object_or_404(Query, pk=query_id)
    outputs = query.output_set.all().order_by('-votes', '-pub_date')
    
    if outputs.count() >= query.amount:
        return render(request, 'main/outputs_partial.html', {
            'outputs': outputs
        })
    else:
        return render(request, 'main/loading_partial.html', {
            'query': query,
            'amount': query.amount
        })