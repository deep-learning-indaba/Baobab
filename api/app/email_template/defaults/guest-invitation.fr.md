---
subject: Votre invitation à {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Nous sommes heureux de vous inviter à {{ event.name }} en qualité de {{ guest.role }}.
{% if event.is_registration_open %}
Pour faciliter l’organisation de l’événement, veuillez remplir notre formulaire d’inscription réservé aux invités dans {{ organisation.system_name }}.

{% button "Remplir le formulaire d'inscription", guest.registration_url %}
{% endif %}
Veuillez répondre à ce courriel si vous avez des questions ou des préoccupations.

Cordialement,
Les organisateurs de {{ event.name }}
