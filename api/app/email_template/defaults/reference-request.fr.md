---
subject: Demande de référence – {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

{% if nominator %}{{ candidate.name }} a été désigné(e) pour participer à {{ event.name }} ({{ event.website_url }}).{% else %}{{ candidate.name }} a présenté sa candidature pour participer à {{ event.name }} ({{ event.website_url }}).{% endif %}

Pour que sa demande puisse être retenue, nous avons besoin d’une lettre de recommandation d’une personne qui connaît {{ candidate.firstname }} à titre professionnel et qui a soutenu sa candidature.

La lettre de référence doit décrire vos rapports avec {{ candidate.firstname }}, indiquer depuis combien de temps vous vous connaissez et préciser le travail accompli par {{ candidate.firstname }} et ce que sa participation apporterait à {{ event.name }}.
Sa demande ne sera **pas** prise en compte si cette lettre de recommandation n’est pas soumise d’ici le {{ reference.deadline }}.

{% button "Téléverser ma lettre de recommandation", reference.url %}

Cordialement,
L’équipe de {{ event.name }}
