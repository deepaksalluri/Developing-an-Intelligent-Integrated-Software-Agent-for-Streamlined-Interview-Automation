from django import forms
# forms.py
class CandidateForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'enter valid email to send result'}))
    job_description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Example :Python Developer'}))


class AnswerForm(forms.Form):
    answer = forms.CharField(widget=forms.Textarea)
