---
subject: {{ event.name }} application status update
---
Dear {{ recipient.salutation }},

Congratulations! You've been selected for **{{ event.name }}**!
{% if offer.grants.size > 0 %}
In addition, we are pleased to offer you the following grants:
{% for grant in offer.grants %}
- **{{ grant.name }}**{% if grant.description %}: {{ grant.description }}{% endif %}
{% endfor %}
{% endif %}
{% for note in offer.notes %}
> **{{ note.name }}**{% if note.description %}: {{ note.description }}{% endif %}
{% endfor %}

**Registration fee:**
{% if offer.payment_required %}In order to confirm your place, you will need to pay a registration fee{% if offer.fee %} of {{ offer.fee.formatted }}{% endif %}.{% else %}Your registration fee has been waived.{% endif %}

You have until **{{ offer.expiry_date }}** to accept the offer, otherwise we will automatically allocate your place to someone else.

{% button "View and accept my offer", offer.url %}

If you are unable to accept the offer for any reason, please let us know on the same page by clicking "Reject" and filling in the reason. We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {{ event.email_from }}.

Kind regards,
The {{ event.name }} organisers
