import os
from django.db import models
from django.utils import timezone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Query(models.Model):
    query = models.CharField(max_length=40000)
    pub_date = models.DateTimeField('Date Published', default=timezone.now)
    amount = models.IntegerField(default=0)

    def __str__(self):
        return self.query
    
    def get_output(self):
        response = client.chat.completions.create(
            model="o3",
            messages=[{"role": "user", "content": self.query}]
        )
        return response.choices[0].message.content

class Output(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    output = models.CharField(max_length=40000)
    pub_date = models.DateTimeField('Date Published', default=timezone.now)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.output