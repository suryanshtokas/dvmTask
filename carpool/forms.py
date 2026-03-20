from django import forms
from .models import CarpoolRequest
from network.models import Node


class CarpoolRequestForm(forms.ModelForm):
    class Meta:
        model = CarpoolRequest
        fields = ["pickup_node", "dropoff_node"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        pickup_node = cleaned_data.get("pickup_node")
        dropoff_node = cleaned_data.get("dropoff_node")

        if pickup_node and dropoff_node:
            if pickup_node == dropoff_node:
                raise forms.ValidationError("Pickup and dropoff nodes cannot be the same.")
            
            if not Node.objects.filter(id=pickup_node.id).exists():
                raise forms.ValidationError("Invalid pickup node.")
            
            if not Node.objects.filter(id=dropoff_node.id).exists():
                raise forms.ValidationError("Invalid dropoff node.")
            
        # stopping same user from creating multiple requests at once (to avoid spam)
        if CarpoolRequest.objects.filter(
            passenger=self.user,
            status__in=["pending", "confirmed"]
        ).exists():
            raise forms.ValidationError("You already have an active carpool request.")
        
        return cleaned_data