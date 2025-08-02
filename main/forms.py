from django import forms

class QueryForm(forms.Form):
    query = forms.CharField(label='Query', max_length=400)
    amount = forms.IntegerField(label='Amount', min_value=1, max_value=50)