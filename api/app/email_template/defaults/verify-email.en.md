---
subject: {{ organisation.system_name }} email verification
---
Dear {{ recipient.salutation }},

Thank you for creating a new {{ organisation.system_name }} account. Please verify your email address using the button below.

{% button "Verify my email address", verification.url %}

If the button doesn't work, copy this link into your browser:
{{ verification.url }}

Kind regards,
{{ organisation.name }}
