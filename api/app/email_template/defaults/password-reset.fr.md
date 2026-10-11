---
subject: Réinitialisation du mot de passe pour {{ organisation.system_name }}
---
Madame / Monsieur {{ recipient.lastname }},

Vous avez récemment demandé une réinitialisation de votre mot de passe sur {{ organisation.system_name }}. Veuillez utiliser le bouton ci-dessous pour choisir un nouveau mot de passe.

{% button "Réinitialiser mon mot de passe", reset.url %}

Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :
{{ reset.url }}

Si vous n’avez pas demandé la réinitialisation de votre mot de passe, veuillez ignorer ce courriel et communiquer avec {{ organisation.name }}.

Cordialement,
{{ organisation.name }}
