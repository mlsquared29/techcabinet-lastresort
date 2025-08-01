from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from .models import Question, Answer

class IndexView(generic.ListView):
    template_name = 'main/index.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        return Question.objects.all()

def question(request, id):
    question = get_object_or_404(Question, pk=id)
    answers = question.answer_set.order_by('-votes')
    return render(request, 'main/question.html', {'question': question, 'answers': answers})

def ask(request):
    q = Question(question_text=request.POST['question'])
    q.save()
    return HttpResponseRedirect(reverse('main:detail', args=(q.id,)))

def answer(request, id):
    q = get_object_or_404(Question, pk=id)
    q.answer_set.create(answer_text=request.POST['answer'])
    return HttpResponseRedirect(reverse('main:detail', args=(q.id,)))

def upvote(request, id, answer_id):
    a = get_object_or_404(Answer, pk=answer_id)
    a.votes += 1
    a.save()
    return HttpResponseRedirect(reverse('main:detail', args=(id,)))

def downvote(request, id, answer_id):
    a = get_object_or_404(Answer, pk=answer_id)
    a.votes -= 1
    a.save()
    return HttpResponseRedirect(reverse('main:detail', args=(id,)))