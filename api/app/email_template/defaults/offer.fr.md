---
subject: Mise à jour de l’état de la demande pour {{ event.name }}
---
Madame / Monsieur {{ recipient.lastname }},

Félicitations ! Votre candidature a été retenue pour **{{ event.name }}** !
{% if offer.grants.size > 0 %}
Votre offre comprend également les subventions suivantes :
{% for grant in offer.grants %}
- **{{ grant.name }}**{% if grant.description %} : {{ grant.description }}{% endif %}
{% endfor %}
{% endif %}
{% for note in offer.notes %}
> **{{ note.name }}**{% if note.description %} : {{ note.description }}{% endif %}
{% endfor %}

**Frais d'inscription :**
{% if offer.payment_required %}Le paiement {% if offer.fee %}de {{ offer.fee.formatted }} {% else %}des frais d'inscription {% endif %}est requis pour confirmer votre place.{% else %}Vos frais d'inscription ont été dispensés.{% endif %}

Vous avez jusqu’au **{{ offer.expiry_date }}** pour accepter l’offre. Dans le cas contraire, nous attribuerons automatiquement votre place à quelqu’un d’autre.

{% button "Consulter et accepter mon offre", offer.url %}

Si vous ne pouvez pas accepter l’offre pour quelque raison que ce soit, veuillez nous en informer sur la même page en cliquant sur le bouton de refus et en précisant la raison. Tous vos commentaires seront lus. Il est possible que nous vous fassions une nouvelle offre par la suite.

Si vous avez des questions, veuillez communiquer avec nous à l’adresse {{ event.email_from }}.

Cordialement,
Les organisateurs de {{ event.name }}
