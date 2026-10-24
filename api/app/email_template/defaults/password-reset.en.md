---
subject: {{ organisation.system_name }} password reset
---
Dear {{ recipient.salutation }},

You recently requested a password reset on {{ organisation.system_name }}. Please use the button below to choose a new password.

{% button "Reset my password", reset.url %}

If the button doesn't work, copy this link into your browser:
{{ reset.url }}

If you did not request a password reset, please ignore this email and contact {{ organisation.name }}.

Kind regards,
{{ organisation.name }}
