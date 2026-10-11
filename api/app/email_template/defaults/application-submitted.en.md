---
subject: {% if event.type == "call" %}Your response to the {{ event.name }}{% else %}Your application for {{ event.name }}{% endif %}
---
Dear {{ recipient.salutation }},

{% if event.type == "call" %}Thank you for responding to the {{ event.name }}.{% else %}Thank you for applying to {{ event.description }}.{% endif %} Your application is being reviewed by our committee and we will get back to you as soon as possible. Included below is a copy of your responses.
{% for section in response.sections %}
### {{ section.name }}
{% for item in section.answers %}
**{{ item.question }}**
{{ item.answer }}
{% endfor %}
{% endfor %}
Kind regards,
The {{ event.name }} team
