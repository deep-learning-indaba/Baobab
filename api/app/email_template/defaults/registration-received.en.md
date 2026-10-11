---
subject: {{ event.name }} registration
---
Dear {{ recipient.salutation }},

Thank you for completing our registration form.
{% if registration.confirmed %}Your place is now confirmed and we look forward to welcoming you at the event!{% else %}Please note that your place is pending confirmation on receipt of payment. You will receive payment instructions in the next few days.{% endif %}
{% if registration.answers.size > 0 %}
Here is a copy of your responses:
{% for item in registration.answers %}
**{{ item.question }}**
{{ item.answer }}
{% endfor %}
{% endif %}
Kind regards,
The {{ event.name }} organisers
