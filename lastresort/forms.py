from django import forms

class PSAEntryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        num_questions = kwargs.pop('num_questions')
        super().__init__(*args, **kwargs)
        for i in range(num_questions):
            self.fields[f'question_{i}'] = forms.CharField(label=f'Question {i+1}', max_length=1000)
            self.fields[f'solution_{i}'] = forms.CharField(label=f'Solution {i+1}', max_length=1000)
            self.fields[f'answer_{i}'] = forms.CharField(label=f'Answer {i+1}', max_length=100)