---
subject: Final reminder to submit your application for {{ event.name }}
---
Dear {{ recipient.salutation }},

We noticed that you started applying to attend {{ event.name }} but have not completed and submitted your application. This is a final reminder that you have until **{{ event.application_close | date: "%A %-d %B %Y" }}** to submit your application in order to be considered.

Please be aware that you must click the Submit button on the final page to confirm your application. If you do not receive an email from us with a copy of your answers, your application will not be considered.

{% button "Continue my application", event.url %}

Kind regards,
The {{ organisation.name }} team
