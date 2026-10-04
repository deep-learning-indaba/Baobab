---
subject: Final reminder: we do not have your application for {{ event.name }}
---
Dear {{ recipient.salutation }},

**We have not received your application to attend {{ event.name }}.**

We noticed that you have created a {{ organisation.system_name }} account, but have not yet started an application to attend {{ event.name }}.
If you think you have already filled in the form, you may not have clicked the Submit button on the final page. If this is the case, we do not have your application and unfortunately you will have to redo it. We sincerely apologise for any confusion.

This is a final reminder that you have until **{{ event.application_close | date: "%A %-d %B %Y" }}** to complete and submit your application.

{% button "Start my application", event.url %}

Kind regards,
The {{ organisation.name }} team
