---
subject: {{ event.name }} offer reset
---
Dear {{ recipient.salutation }},

Your offer for {{ event.name }} has been reset, so you can respond to it again. Please accept or decline your offer by **{{ offer.expiry_date }}**.

{% button "View my offer", offer.url %}

If you have any questions, contact us at {{ event.email_from }}.

Kind regards,
The {{ event.name }} organisers
