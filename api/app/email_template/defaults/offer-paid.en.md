---
subject: {{ event.name }} payment received
---
Dear {{ recipient.salutation }},

Thank you for your payment. We have now received your registration fee for {{ event.name }}. You may now complete your registration.

{% button "Complete my registration", event.registration_url %}

Kind regards,
The {{ event.name }} organisers
