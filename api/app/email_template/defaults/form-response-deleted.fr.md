---
subject: Votre réponse au formulaire {{ form.name }} a été supprimée
---
Madame / Monsieur {{ recipient.lastname }},

Cet e-mail a pour but de vous informer que votre réponse au formulaire « {{ form.name }} » pour {{ event.name }} a été supprimée par les organisateurs.

Si vous pensez qu'il s'agit d'une erreur, veuillez contacter les organisateurs à l'adresse {{ event.email_from }}.

Cordialement,
Les organisateurs de {{ event.name }}
