---
subject: {{ event.name }} registration confirmation
---
Dear {{ recipient.salutation }},

Thank you for completing your guest registration.
{% if registration.answers.size > 0 %}
Here is a copy of your responses:
{% for item in registration.answers %}
**{{ item.question }}**
{{ item.answer }}
{% endfor %}
{% endif %}
Kind regards,
The {{ event.name }} team
