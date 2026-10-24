---
subject: Your invitation to {{ event.name }}
---
Dear {{ recipient.salutation }},

We are pleased to invite you to attend {{ event.name }} as a {{ guest.role }}.
Please follow these steps to access our event management system, {{ organisation.system_name }}:

1. Set your account password using the button below.
2. Log in using your email address (the one you received this email on) and your new password.
{% if event.is_registration_open %}3. Complete the guest registration form: {{ guest.registration_url }}
4. Update your details: {{ account.profile_url }}{% else %}3. Update your details: {{ account.profile_url }}{% endif %}

{% button "Set my password", account.set_password_url %}

Please reply to this email should you have any questions or concerns.

Kind regards,
The {{ event.name }} organisers
