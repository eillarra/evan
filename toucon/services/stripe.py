import json
import stripe

from django.conf import settings
from os import environ

from toucon.models import Registration, Payment


SUPPORTED_CURRENCIES = (  # https://stripe.com/docs/currencies
    ('EUR', 'Euro'),
    ('USD', 'USD')
)

stripe.api_key = environ.get('STRIPE_SECRET_KEY')


def create_charge(registration: Registration, amount: int, token: str) -> stripe.Charge:
    """
    Given a Registration and a Stripe token (via JS) create a Stripe Charge.
    A meaningful description and some extra metadata is added to have better information at stripe.com.
    """
    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency=registration.conference.currency.lower(),
            source=token,
            receipt_email=registration.user.email,
            description='[{0}] Registration {1}'.format(registration.conference.code, registration.uuid),
            metadata={
                'user': 'user_{0} <{1}>'.format(registration.user_id, registration.user.email),
                'conference': registration.conference.code,
                'registration': registration.uuid,
            }
        )

        status = charge.status
        outcome, stripe_id, stripe_response = charge.outcome.seller_message, charge.id, json.dumps(charge)

    except Exception as e:
        res = e.json_body
        status = Payment.FAILED
        outcome, stripe_id, stripe_response = res['error']['message'], res['error']['charge'], res

    payment = Payment.objects.create(
        registration=registration,
        currency=registration.conference.currency,
        amount=amount,
        type=Payment.STRIPE_CHARGE,
        status=status,
        outcome=outcome,
        stripe_id=stripe_id,
        stripe_response=stripe_response,
    )

    if payment.status == Payment.FAILED:
        raise Exception(payment.outcome)
    else:
        return payment
