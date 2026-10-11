---
subject: Votre invitation à {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Nous sommes heureux de vous inviter à {{ event.name }} en qualité de {{ guest.role }}.
Veuillez suivre les étapes ci-dessous pour accéder à notre système de gestion des événements, {{ organisation.system_name }} :

1. Créez votre mot de passe à l’aide du bouton ci-dessous.
2. Ouvrez une session avec votre adresse électronique (celle sur laquelle vous avez reçu ce courriel) et votre nouveau mot de passe.
{% if event.is_registration_open %}3. Remplissez le formulaire d’inscription des invités : {{ guest.registration_url }}
4. Mettez à jour vos coordonnées : {{ account.profile_url }}{% else %}3. Mettez à jour vos coordonnées : {{ account.profile_url }}{% endif %}

{% button "Créer mon mot de passe", account.set_password_url %}

Veuillez répondre à ce courriel si vous avez des questions ou des préoccupations.

Cordialement,
Les organisateurs de {{ event.name }}
