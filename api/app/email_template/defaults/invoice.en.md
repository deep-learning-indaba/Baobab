---
subject: {{ event.name }} invoice {{ invoice.number }}
---
Dear {{ recipient.salutation }},

Please find attached invoice **{{ invoice.number }}** for {{ invoice.total }}, for your registration at {{ event.name }}.

Payment is due by **{{ invoice.due_date }}**.

{% button "Pay now", invoice.payment_url %}

If you have any questions, contact us at {{ event.email_from }}.

Kind regards,
The {{ event.name }} organisers
