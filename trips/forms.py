from django import forms
from .models import Trip
from network.models import Node


class TripCreateForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ["start_node", "end_node", "max_passengers"]

    def clean(self):
        cleaned_data = super().clean()
        start_node = cleaned_data.get("start_node")
        end_node = cleaned_data.get("end_node")

        if start_node and end_node and start_node == end_node:
            raise forms.ValidationError("Start and end nodes cannot be the same.")
        
        return cleaned_data