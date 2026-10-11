---
subject: Votre {{ document.name }} pour {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Votre {{ document.name }} pour {{ event.name }} est prêt. Vous pouvez aussi le télécharger à tout moment depuis {{ organisation.system_name }}.

{% button "Voir mes documents", document.url %}

Cordialement,
L’équipe {{ event.name }}
