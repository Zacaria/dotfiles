# Revue du dépôt et migration chezmoi

Objectif : réinstaller facilement l'environnement macOS. Revue séquentielle sous les angles correction, fiabilité, sécurité, maintenabilité et automatisation.

## Défauts de départ corrigés

| Priorité | Élément initial | Défaut vérifié | État final |
| --- | --- | --- | --- |
| P1 | install.sh | Copies sans sauvegarde et chemins dépendants du répertoire courant | Gestion native chezmoi ; diff, application ciblée et détection des conflits |
| P1 | install.sh | exec zsh interrompait le processus avant la fin | Scripts chezmoi ordonnés avant l'application des fichiers |
| P1 | install.sh | Test de clé SSH avec un tilde entre guillemets, puis génération inattendue | Aucune génération de clé ; accès restaurés séparément |
| P1 | Polices | Le clone et rm -rf fonts pouvaient supprimer des fichiers suivis | Police déclarée dans home/dot_Brewfile ; dossier historique conservé |
| P2 | Shell et n | URL raccourcie, chemins du Mac et managers concurrents | Sources portables dans home/, runtimes dans mise et Python dans uv |
| P2 | Git | Adresse vide, option incorrecte en doublon, chemin absolu | Identité locale séparée et configuration portable |
| P2 | Ignore global | Masquait .vscode et graphql.config.json dans tous les projets | Ignore limité aux fichiers locaux et secrets |
| P2 | Installation | Aucune vérification de réexécution ou d'échec partiel | Huit tests avec chezmoi réel, scripts idempotents et contrôles en CI |
| P3 | Éditeurs et terminaux historiques | Réglages devenus inutiles avec le passage à Zed et Ghostty | Neovim retiré du Brewfile ; configurations VS Code/iTerm retirées ; réglages Zed/Ghostty portables inclus |
| P3 | Documentation | Liste de TODO sans procédure | Guide chezmoi, restauration et propositions d'ajouts |

## Architecture finale

.chezmoiroot désigne home/ comme racine des sources. Les préfixes dot_ deviennent les fichiers cachés du HOME. Les fichiers sont gérés en mode copie, sans code maison de liens.

Le script run_onchange_before_10-install-environment.sh.tmpl inclut les empreintes du Brewfile, de la configuration mise et de la version Python uv. Il installe les dépendances avant d'écrire les fichiers, sans mise à niveau globale Homebrew. uv peut être mis à niveau si l'option --default manque. Le script run_once_before_20-install-oh-my-zsh.sh.tmpl prépare Oh My Zsh s'il manque.

Le script run_onchange_after_30-configure-agents.sh.tmpl configure context-mode 2.1.0 et RTK sur Codex et Oh My Pi. RTK peut être mis à niveau si son intégration native Oh My Pi manque. Les hooks context-mode sont approuvés par son setup ; scripts/trust-codex-rtk.mjs utilise l'API app-server de Codex pour approuver uniquement le hook global de commande exacte rtk hook codex, avec l'empreinte retournée par Codex. Les autres hooks et les réglages de sandbox sont conservés.

Le paquet context-mode est installé dans un préfixe npm stable, hors de l'installation Node. La politique npm de délai de publication est respectée. Le chargement Oh My Pi passe par le manifeste compatible Pi du paquet. Un wrapper temporaire limite uniquement codex plugin list au marketplace context-mode pour éviter la limite de sortie du setup ; les autres commandes sont déléguées au vrai Codex.

La configuration locale chezmoi garde ~/repos/dotfiles comme dépôt source. Les trois fichiers mise/uv ont été appliqués sur le Mac courant et les agents configurés ; les onze autres fichiers personnels restent à comparer avant une application complète.

## Vérification

bash scripts/check.sh valide les syntaxes Bash/zsh, le Brewfile, Git, le JSON Zed et les TOML mise/uv/Bun. Les scripts sont rendus par chezmoi avant leur passage dans ShellCheck et shfmt.

Les huit tests utilisent le vrai chezmoi avec un HOME et une base d'état isolés : périmètre des fichiers gérés, simulation sans exécution, application répétable, fichiers locaux conservés, arrêt sur conflit, configuration du dépôt source, chemins avec espaces, échec des dépendances et relance des scripts sur changement de manifeste.

Quatre tests Node couvrent la sélection stricte du hook RTK, ses empreintes et son état de confiance. Le bootstrap teste aussi le protocole JSON-RPC avec un faux app-server, ainsi que l'ordre des installations et configurations, sans contacter de services externes.

La CI macOS utilise une action checkout figée sur un SHA et un jeton en lecture seule, sans conservation des identifiants Git. Un scan du dépôt de travail n'a détecté aucun secret ; il ne remplace pas un audit complet de l'historique Git.

Sur ce Mac, Python 3.13.3 s'exécute depuis uv ; les six autres runtimes et Oh My Pi sont disponibles sous mise. Zed et Codex CLI sont présents. context-mode expose ses neuf outils dans le chargeur compatible Pi ; un appel réel ctx_execute a réussi. L'extension RTK réécrit git status en rtk git status. Codex annonce le hook RTK et les quatre hooks context-mode comme approuvés. Aucun appel de modèle payant ni restauration sur un Mac vierge n'a été utilisé pour ces vérifications.

Deux avertissements n'empêchent pas le chargement : Oh My Pi signale l'absence de package.json à la racine des plugins liés localement ; RTK ne peut pas préparer sa base de statistiques depuis le sandbox de cet agent. Aucune permission Codex supplémentaire n'a été ajoutée pour les statistiques.

## Éléments conservés et propositions

Les polices et licences historiques restent dans fonts/. La modification préexistante de fonts/.DS_Store est conservée. L'ancien export iTerm et la configuration VS Code ont été retirés du dépôt. Aucun logiciel existant du Mac n'a été désinstallé.

Le choix de Zed et Ghostty est reflété dans le Brewfile, les fichiers gérés et les réglages de l'éditeur Git/shell. La configuration Zed exclut notamment les connexions SSH et les réglages d'agents. Les politiques npm/Bun sont versionnées sans tokens, avec un délai de sept jours et sans exception permanente. Les modèles SSH/GPG restent à personnaliser localement.

La vérification locale a confirmé que npm 11.19.1 utilise min-release-age en jours ; l'ancienne clé minimum-release-age était ignorée. Le fichier portable garde uniquement min-release-age=7 et save-exact=true. La commande zed était absente du PATH de ce Mac : un lien vers le lanceur officiel de l'application la rend disponible sans réinstaller Zed.

Les applications, profils d'éditeur, terminaux, règles npm et accès SSH/GPG à ajouter sont détaillés dans [la checklist](restore-checklist.md). Leur import reste une proposition ; aucun secret n'a été copié dans les sources.

## Références

- [Chezmoi : prise en main](https://www.chezmoi.io/quick-start/)
- [Racine des sources](https://www.chezmoi.io/reference/special-files/chezmoiroot/)
- [Scripts et empreintes de manifestes](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)
- [Mise : versions globales](https://mise.jdx.dev/configuration.html)
