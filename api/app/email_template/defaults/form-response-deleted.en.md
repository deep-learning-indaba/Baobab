---
subject: Your response to {{ form.name }} has been deleted
---
Dear {{ recipient.salutation }},

This email is to let you know that your response to the form "{{ form.name }}" for {{ event.name }} has been deleted by the organisers.

If you believe this was a mistake, please get in touch with the organisers at {{ event.email_from }}.

Kind regards,
The {{ event.name }} organisers
