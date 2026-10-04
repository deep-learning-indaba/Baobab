---
subject: Des tâches de révision vous ont été attribuées dans {{ organisation.system_name }}
---
Madame / Monsieur {{ recipient.lastname }},

{{ reviews.count }} tâches de révision vous ont été attribuées dans {{ organisation.system_name }}.

{% button "Commencer les révisions", reviews.url %}

Merci de nous aider à passer en revue les demandes pour {{ event.name }} !

Cordialement,
Les organisateurs de {{ event.name }}
