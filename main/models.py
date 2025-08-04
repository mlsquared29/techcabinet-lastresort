import os
from django.db import models
from django.utils import timezone
from openai import OpenAI
from dotenv import load_dotenv
from django.contrib.auth.models import User

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Competition(models.Model):
    user = models.ManyToManyField(User, related_name='competitions')
    name = models.CharField(max_length=100)
    short_description = models.CharField(max_length=1000)
    description = models.TextField()
    num_questions = models.IntegerField(default=1)
    pub_date = models.DateTimeField('Date Published', default=timezone.now)
    end_date = models.DateTimeField('Date Ended', default=timezone.now)
    is_active = models.BooleanField(default=True)

    def is_past_end_date(self):
        return timezone.now() > self.end_date

    def save(self, *args, **kwargs):
        if self.is_past_end_date():
            self.is_active = False
        super().save(*args, **kwargs)

class PSAGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    pub_date = models.DateTimeField('Date Published', default=timezone.now)

    def __str__(self):
        return self.name

class PSAEntry(models.Model):
    group = models.ForeignKey(PSAGroup, on_delete=models.CASCADE)
    problem = models.CharField(max_length=1000)
    solution = models.CharField(max_length=1000)
    answer = models.CharField(max_length=100)
    pub_date = models.DateTimeField('Date Published', default=timezone.now)

    def __str__(self):
        return f'{self.problem} - {self.solution} - {self.answer}'
    
    def get_ai_solution_and_answer(self):
        response = client.responses.create(
            model="gpt-4o",
            input=f"Solve the following problem. Output ONLY your final answer on the last line after your solution. It must only be the answer, no other text. The answer must have zero formatting. {self.problem}"
        )
        response_text = response.output_text
        return (response_text, response_text.split('\n')[-1])

class AIResponse(models.Model):
    psa_entry = models.ForeignKey(PSAEntry, on_delete=models.CASCADE)
    ai_solution = models.CharField(max_length=40000)
    ai_answer = models.CharField(max_length=100)
    pub_date = models.DateTimeField('Date Published', default=timezone.now)

    def __str__(self):
        return f'{self.ai_solution} - {self.ai_answer}'