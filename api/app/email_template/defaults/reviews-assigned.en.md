---
subject: You have been assigned reviews for {{ event.name }}
---
Dear {{ recipient.salutation }},

You have been assigned {{ reviews.count }} reviews on {{ organisation.system_name }}.

{% button "Start reviewing", reviews.url %}

Thank you for helping us review applications for {{ event.name }}!

Kind regards,
The {{ event.name }} organisers
