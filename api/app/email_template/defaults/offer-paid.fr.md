---
subject: {{ event.name }} : paiement reçu
---
Madame / Monsieur {{ recipient.lastname }},

Merci pour votre paiement. Nous avons bien reçu vos frais d'inscription pour {{ event.name }}. Vous pouvez maintenant compléter votre inscription.

{% button "Compléter mon inscription", event.registration_url %}

Cordialement,
Les organisateurs de {{ event.name }}
