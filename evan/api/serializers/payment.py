from rest_framework import serializers

from evan.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('amount', 'status', 'outcome')
