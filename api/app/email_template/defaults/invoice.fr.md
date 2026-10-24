---
subject: {{ event.name }} : facture {{ invoice.number }}
---
Madame / Monsieur {{ recipient.lastname }},

Veuillez trouver ci-joint la facture **{{ invoice.number }}** d’un montant de {{ invoice.total }} pour votre inscription à {{ event.name }}.

Le paiement est dû au plus tard le **{{ invoice.due_date }}**.

{% button "Payer maintenant", invoice.payment_url %}

Si vous avez des questions, contactez-nous à {{ event.email_from }}.

Cordialement,
Les organisateurs de {{ event.name }}
