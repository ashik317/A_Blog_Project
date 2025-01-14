from django import forms

class EmailPostForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)


