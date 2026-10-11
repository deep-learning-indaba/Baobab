---
subject: Inscription à {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Merci d’avoir rempli le formulaire d’inscription.
{% if registration.confirmed %}Votre place est maintenant confirmée et nous nous réjouissons de vous accueillir à l'événement !{% else %}Veuillez noter que votre place est en attente de confirmation à la réception du paiement. Vous recevrez les instructions de paiement dans les prochains jours.{% endif %}
{% if registration.answers.size > 0 %}
Voici une copie de vos réponses :
{% for item in registration.answers %}
**{{ item.question }}**
{{ item.answer }}
{% endfor %}
{% endif %}
Cordialement,
Les organisateurs de {{ event.name }}
