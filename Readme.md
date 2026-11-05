# Dotfiles avec chezmoi

Kit de réinstallation macOS : **chezmoi gère les fichiers**, **mise sélectionne les runtimes et Oh My Pi**, **uv gère Python**, **Brewfile décrit les paquets**. Les chemins Homebrew sont adaptés à Apple Silicon et Intel.

## Réinstaller

Installer les [Xcode Command Line Tools](https://developer.apple.com/xcode/resources/), Homebrew, puis chezmoi :

    brew install chezmoi

Après avoir cloné ce dépôt dans ~/repos/dotfiles :

    chezmoi init --source "$HOME/repos/dotfiles"
    chezmoi diff
    chezmoi apply --less-interactive
    exec zsh -l

Sur une machine neuve, on peut aussi utiliser chezmoi init --apply avec l'URL du dépôt, et --source pour choisir l'emplacement du clone. La [documentation officielle](https://www.chezmoi.io/quick-start/) décrit cette installation en une commande.

Pour simuler sans modifier les fichiers ni exécuter les scripts :

    chezmoi apply --dry-run --verbose

Pour appliquer uniquement les fichiers, sans installer de paquet :

    chezmoi apply --exclude=scripts --less-interactive

Chezmoi signale les modifications externes aux fichiers déjà gérés. Dans une automatisation, utiliser --error-on-conflict pour arrêter l'opération plutôt qu'écraser une modification locale. Sur une machine existante, lire le diff avant une première application.

## Organisation

Le fichier .chezmoiroot limite les sources à home/. Les documents, tests, anciennes polices et profils d'éditeur du dépôt ne sont pas déployés dans le HOME.

- home/dot_zshrc, home/dot_zprofile : shell portable et activation mise.
- home/dot_aliases, home/dot_gitconfig, home/dot_gitignore_global : réglages communs.
- home/dot_config/mise/config.toml : versions globales de Node, Bun, Java, Go, Rust, Julia et Oh My Pi.
- home/dot_config/uv/ : version Python globale et préférence pour les interpréteurs gérés par uv.
- home/dot_config/zed/settings.json et home/dot_config/ghostty/config.ghostty : réglages portables de l'IDE et du terminal.
- home/dot_npmrc et home/dot_bunfig.toml : délai de publication de sept jours ; npm enregistre aussi les versions exactes.
- home/dot_Brewfile : paquets, déployé en ~/.Brewfile.
- home/.chezmoiscripts/ : installation des paquets et interpréteurs avant application, puis configuration des agents après application ; relance lors des changements de manifestes. Oh My Zsh est préparé une seule fois.
- docs/ : [revue](docs/review.md), [restauration et ajouts proposés](docs/restore-checklist.md).

Chezmoi utilise son mode fichier : les configurations du HOME sont des copies gérées, pas des liens vers le dépôt. Aucun gestionnaire maison de liens ou script install.sh n'est nécessaire.

## Modifier la configuration

    chezmoi edit ~/.config/mise/config.toml
    chezmoi diff
    chezmoi apply

Pour une modification faite directement dans le HOME, notamment avec mise use --global, récupérer la modification dans les sources :

    chezmoi re-add ~/.config/mise/config.toml
    chezmoi diff

Les projets peuvent choisir leurs versions dans mise.toml et les fichiers de versions activés. Node suit la branche 24 ; les autres valeurs sont les versions exactes conservées lors de la migration. Les configurations de projets priment sur les valeurs globales.

Python est sélectionné par uv, avec 3.13.3 comme défaut global dans ~/.config/uv/.python-version. Dans un projet, utiliser uv python pin et uv sync ; uv run python exécute son interpréteur. Le bootstrap installe aussi les commandes python et python3 avec uv python install --default. Les shims Python de mise sont exclus pour éviter une concurrence sur le PATH. Après une modification du défaut uv, récupérer les fichiers avec chezmoi re-add ~/.config/uv.

## Éditeurs et agents

Un seul Brewfile décrit les applications et outils retenus : **Zed**, **Ghostty**, **Codex CLI**, uv, RTK et les outils de développement. Oh My Pi est installé par le backend GitHub de mise, version 18.16.0. Les installations manuelles existantes de Zed et Ghostty dans /Applications sont conservées. Le bootstrap rend aussi disponible la commande zed si le lanceur manque.

Zed est l'éditeur du shell et de Git, avec zed --wait pour attendre la fermeture du fichier avant de terminer un commit. Les sources conservent l'enregistrement au changement de focus, les tailles de police et le thème du Mac actuel ; connexions SSH, comptes et réglages d'agents restent locaux. Ghostty reprend les réglages de police, marges, curseur, presse-papiers et intégration shell. Neovim, VS Code et iTerm ont été retirés du bootstrap et leurs anciennes configurations du dépôt.

Le script après application configure **context-mode 2.1.0** et **RTK** sur Codex et Oh My Pi :

- Codex utilise le marketplace et le plugin natifs context-mode. Son setup approuve les hooks du plugin.
- Oh My Pi charge le même paquet local via sa compatibilité avec les extensions Pi.
- RTK installe son hook Codex et son extension native Oh My Pi. La confiance Codex est enregistrée pour la commande exacte rtk hook codex du fichier global, avec son empreinte courante.

context-mode est installé dans ~/.local/lib/node_modules et son exécutable dans ~/.local/bin, afin de survivre aux changements de Node. Sa version est déclarée dans home/.chezmoidata.toml. npm conserve la politique locale de délai de publication : aucun contournement permanent n'est ajouté. Si cette politique bloque une nouvelle version épinglée, l'installation s'arrête ; attendre qu'elle soit éligible ou décider séparément d'une exception ponctuelle.

Les paquets Homebrew existants sont conservés par défaut ; uv et RTK peuvent être mis à niveau si leurs fonctionnalités de setup requises manquent. Les configurations d'authentification restent locales. Après installation, redémarrer Codex et Oh My Pi pour charger leurs hooks et extensions.

Les changements Git restent explicites : chezmoi ne committe ni ne pousse automatiquement.

## Réglages personnels et accès

~/.zshrc.local, ~/.zprofile.local et ~/.gitconfig.local restent locaux. Les fichiers shell les chargent avant l'activation de mise. Le modèle .gitconfig.local.example aide à restaurer l'identité et la signature Git après récupération des clés.

Les clés privées et tokens viennent d'une sauvegarde chiffrée ou d'un gestionnaire de secrets. La checklist décrit la restauration SSH/GPG ; docs/ssh-config.example fournit un modèle sans hôte réel. GnuPG est installé par le Brewfile.

Sur le Mac ayant servi à la migration, les configurations mise et uv ont été appliquées, et les intégrations des agents configurées. Les onze autres fichiers portables restent à comparer avant une application complète, notamment pour conserver les ajouts privés des configurations Zed et npm. Les sauvegardes du shell, des exécutables remplacés et des configurations d'agents sont dans ~/.local/state/chezmoi-migration/ et ~/.local/state/mise-runtime-migration/.

## Vérifier

    bash scripts/check.sh

Python 3.11 ou ultérieur, Node 18 ou ultérieur, chezmoi, zsh et Ruby sont requis. ShellCheck et shfmt sont fournis par le Brewfile et la CI. Huit tests utilisent le vrai binaire chezmoi dans des HOME, caches et bases d'état temporaires. Ils vérifient les conflits, les chemins avec espaces, les scripts, leur relance et l'absence d'écriture en simulation. Quatre tests Node vérifient le périmètre strict de la confiance du hook RTK ; l'échange avec app-server est également simulé dans le test du bootstrap.

Une restauration complète sur un Mac vierge reste la validation finale ; comptes, authentification et préférences macOS suivent la checklist.
