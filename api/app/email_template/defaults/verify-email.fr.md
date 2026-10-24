---
subject: Vérification de votre adresse électronique {{ organisation.system_name }}
---
Madame / Monsieur {{ recipient.lastname }},

Merci d’avoir créé un nouveau compte {{ organisation.system_name }}. Veuillez vérifier votre adresse électronique à l’aide du bouton ci-dessous.

{% button "Vérifier mon adresse électronique", verification.url %}

Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :
{{ verification.url }}

Cordialement,
{{ organisation.name }}
