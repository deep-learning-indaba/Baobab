---
subject: Dernier rappel pour soumettre votre candidature à {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Nous avons remarqué que vous avez commencé une candidature pour {{ event.name }} sans la soumettre. Ceci est un dernier rappel : vous avez jusqu’au **{{ event.application_close | date: "%A %-d %B %Y" }}** pour soumettre votre candidature afin qu’elle soit prise en compte.

Veuillez noter que vous devez cliquer sur le bouton Soumettre de la dernière page pour confirmer votre candidature. Si vous ne recevez pas de courriel de notre part avec une copie de vos réponses, votre candidature ne sera pas prise en compte.

{% button "Poursuivre ma candidature", event.url %}

Cordialement,
L’équipe {{ organisation.name }}
