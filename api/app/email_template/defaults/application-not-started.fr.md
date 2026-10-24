---
subject: Dernier rappel : nous n’avons pas reçu votre candidature pour {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

**Nous n’avons pas reçu votre candidature pour {{ event.name }}.**

Nous avons remarqué que vous avez créé un compte {{ organisation.system_name }} mais que vous n’avez pas encore commencé de candidature pour {{ event.name }}.
Si vous pensez avoir déjà rempli le formulaire, il est possible que vous n’ayez pas cliqué sur le bouton Soumettre de la dernière page. Dans ce cas, nous n’avons pas votre candidature et vous devrez malheureusement la refaire. Nous nous excusons sincèrement pour ce désagrément.

Ceci est un dernier rappel : vous avez jusqu’au **{{ event.application_close | date: "%A %-d %B %Y" }}** pour remplir et soumettre votre candidature.

{% button "Commencer ma candidature", event.url %}

Cordialement,
L’équipe {{ organisation.name }}
