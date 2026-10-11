---
subject: Inscription à {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Merci d’avoir rempli le formulaire d’inscription pour les invités.
{% if registration.answers.size > 0 %}
Voici une copie de vos réponses :
{% for item in registration.answers %}
**{{ item.question }}**
{{ item.answer }}
{% endfor %}
{% endif %}
Cordialement,
L’équipe {{ event.name }}
