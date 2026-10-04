---
subject: Votre demande pour {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Merci d’avoir soumis votre demande de participation à {% if event.type == "call" %}{{ event.name }}{% else %}{{ event.description }}{% endif %}. Votre demande sera examinée par notre comité et nous vous répondrons dès que possible. Vous trouverez ci-dessous une copie de vos réponses.
{% for section in response.sections %}
### {{ section.name }}
{% for item in section.answers %}
**{{ item.question }}**
{{ item.answer }}
{% endfor %}
{% endfor %}
Cordialement,
L’équipe de {{ event.name }}
