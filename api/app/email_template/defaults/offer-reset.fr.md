---
subject: {{ event.name }} : offre réinitialisée
---
Madame / Monsieur {{ recipient.lastname }},

Votre offre pour {{ event.name }} a été réinitialisée, vous pouvez donc y répondre à nouveau. Veuillez accepter ou refuser votre offre avant le **{{ offer.expiry_date }}**.

{% button "Consulter mon offre", offer.url %}

Si vous avez des questions, contactez-nous à {{ event.email_from }}.

Cordialement,
Les organisateurs de {{ event.name }}
