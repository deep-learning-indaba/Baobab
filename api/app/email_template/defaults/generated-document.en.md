---
subject: Your {{ document.name }} for {{ event.name }}
---
Dear {{ recipient.salutation }},

Your {{ document.name }} for {{ event.name }} is ready. You can also download it at any time from {{ organisation.system_name }}.

{% button "View my documents", document.url %}

Kind regards,
The {{ event.name }} team
