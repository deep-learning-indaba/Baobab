---
subject: Your invitation to {{ event.name }}
---
Dear {{ recipient.salutation }},

We are pleased to invite you to attend {{ event.name }} as a {{ guest.role }}.
{% if event.is_registration_open %}
To assist with our planning, please complete our guest registration form in {{ organisation.system_name }}.

{% button "Complete guest registration", guest.registration_url %}
{% endif %}
Please reply to this email should you have any questions or concerns.

Kind regards,
The {{ event.name }} organisers
