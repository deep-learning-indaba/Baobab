---
subject: Reference request for {{ event.name }}
---
Dear {{ recipient.salutation }},

{% if nominator %}{{ candidate.name }} has been nominated by {{ nominator.name }}{% else %}{{ candidate.name }} has nominated themselves{% endif %} for the {{ event.name }} ({{ event.website_url }}).
In order for their application to be considered, we require a reference letter from someone who knows {{ candidate.firstname }} in a professional capacity, and they have selected you.

The reference letter should describe your relationship to {{ candidate.firstname }}, how long you've known them, and should comment on the work {{ candidate.firstname }} has done and its worthiness of the {{ event.name }}.
Their application will **not** be considered if this reference letter is not submitted by {{ reference.deadline }}.

{% button "Upload my reference letter", reference.url %}

Kind regards,
The {{ event.name }} team
