# Réinstaller le Mac

## Base déjà automatisée

Chezmoi déploie quatorze fichiers décrits dans home/. Les scripts avant application installent les paquets du Brewfile, les runtimes mise, Python via uv et Oh My Zsh. Après application, context-mode et RTK sont configurés sur Codex et Oh My Pi. Le contenu des manifestes déclenche la relance des scripts concernés.

    chezmoi init --source "$HOME/repos/dotfiles"
    chezmoi diff
    chezmoi apply --dry-run --verbose
    chezmoi apply --less-interactive
    exec zsh -l

Homebrew, les Xcode Command Line Tools et chezmoi sont des prérequis. Aucun script ne change le shell système, ne génère de clé SSH ou ne modifie les préférences macOS. Homebrew Bundle conserve les paquets existants ; seuls uv et RTK peuvent être mis à niveau si leurs fonctionnalités de setup requises manquent.

Zed, Ghostty et Codex CLI sont déclarés dans le Brewfile. Oh My Pi 18.16.0 est épinglé dans mise. context-mode 2.1.0 est épinglé dans home/.chezmoidata.toml, installé dans ~/.local, puis lié comme plugin compatible Pi dans Oh My Pi et installé comme plugin natif dans Codex. RTK utilise ses intégrations natives pour chaque agent. La confiance est limitée aux hooks de ces intégrations ; aucune clé d'API ni session n'est versionnée.

La politique npm locale est respectée. Une version context-mode encore trop récente pour cette politique interrompt le setup ; attendre sa disponibilité ou décider d'une exception ponctuelle distincte. Redémarrer les deux agents après le setup et vérifier context-mode doctor, rtk init --global --codex --show et omp plugin doctor.

Les fichiers personnels restent dans ~/.zshrc.local, ~/.zprofile.local et ~/.gitconfig.local. Les deux premiers sont chargés avant l'activation de mise, qui garde la priorité sur les anciens runtimes.

## Choix retenus

1. **Applications** : un seul fichier home/dot_Brewfile liste les outils à réinstaller. Aucun second fichier Brewfile.apps n'est nécessaire. Docker, Postman et l'application Xcode ne sont pas ajoutés automatiquement.
2. **IDE : Zed**. Il remplace Neovim et VS Code. Le dépôt configure l'éditeur Git et les variables EDITOR/VISUAL avec zed --wait, afin que Git attende la fermeture du fichier. Les réglages Zed repris concernent l'apparence et l'enregistrement automatique ; les connexions SSH et comptes restent locaux.
3. **Terminal : Ghostty**. Il remplace iTerm. L'application et ses réglages de police, marges, curseur, presse-papiers et intégration shell sont inclus. Une installation manuelle déjà présente dans /Applications est conservée.
4. **Accès SSH et signature GPG conservés**. GnuPG figure dans le Brewfile. Les clés privées sont restaurées depuis une sauvegarde chiffrée ; le dépôt fournit .gitconfig.local.example et docs/ssh-config.example comme modèles à personnaliser.
5. **Règles npm/Bun conservées**. Les nouvelles versions doivent avoir au moins sept jours avant installation : min-release-age=7 jours pour npm et minimumReleaseAge=604800 secondes pour Bun. save-exact=true enregistre les versions exactes lors des ajouts npm. Ces réglages sont déployés par chezmoi ; tokens et accès aux registres restent locaux. Aucun paquet n'est exempté de façon permanente. L'ancienne clé minimum-release-age, ignorée par npm, n'est pas reprise dans le fichier portable.

Sur une machine existante, comparer particulièrement les fichiers Zed et npm avant application pour préserver les réglages privés déjà présents. Sur ce Mac, ils n'ont pas été remplacés par les versions portables du dépôt.

## Autres ajouts proposés

Ces éléments ont été repérés le 5 novembre 2026. Ils restent optionnels ; leurs contenus personnels n'ont pas été importés.

| Priorité | Élément observé | Ajout proposé | Précaution |
| --- | --- | --- | --- |
| Moyenne | Docker, Postman et Xcode installés | Ajouter les applications réellement utiles au Brewfile ; Xcode via l'App Store | Ne pas réinstaller toutes les applications historiques par défaut |
| Moyenne | Alias personnels de connexions et tunnels SSH | Garder les alias génériques dans .aliases ; modèles locaux pour les connexions | Ne pas publier les IP, noms de machines ou chemins de clés |
| Moyenne | Outils mobiles, compilation et embarqué : CMake, LLVM, Ninja, CocoaPods, XcodeGen, outils iOS/USB | Choisir les outils utiles avant de les ajouter au manifeste | Ne pas imposer tous les SDK à chaque machine |
| Moyenne | pnpm, Yarn, outils npm/Cargo/uv installés à part | Inventaire choisi des CLI, puis versions déclarées via les backends mise adaptés | Ne pas copier les répertoires de paquets globaux |
| Moyenne | Règles, skills et autres plugins des assistants de développement | Sélectionner les règles communes en complément de context-mode et RTK déjà automatisés | Exclure historique des chats, bases locales, sessions et authentification |
| Basse | Préférences clavier, captures d'écran, Dock/Finder | Un script macOS séparé et optionnel, avec mode simulation | Choisir les réglages à appliquer ; éviter un export massif de defaults |

La configuration Starship actuelle est vide : le fichier versionné conserve les valeurs par défaut. Aucun thème supplémentaire n'est à récupérer pour le moment.

## Identité et accès après restauration

1. Restaurer les clés SSH/GPG depuis le stockage chiffré et vérifier leurs permissions.
   Pour SSH, garder ~/.ssh en mode 700 et les clés privées en mode 600 ; adapter le modèle docs/ssh-config.example sans publier les hôtes réels. Pour GPG, importer la clé privée depuis la sauvegarde avec gpg --import, puis retrouver son identifiant avec gpg --list-secret-keys --keyid-format LONG.
2. Copier .gitconfig.local.example vers ~/.gitconfig.local, puis renseigner l'identité réelle.
3. Activer la signature des commits dans ce fichier local après avoir restauré la clé.
4. Se reconnecter à GitHub, aux registres de paquets et aux applications.
5. Installer les applications optionnelles choisies et importer leurs profils nettoyés.
6. Configurer Zed pour utiliser les runtimes mise et les environnements uv, puis redémarrer les applications et les agents.

Les interpréteurs système Ruby, Perl et Swift restent fournis par macOS/Xcode. Ruby Homebrew et LuaJIT sont présents comme dépendances ; ils ne deviennent pas des valeurs globales. Mono reste sous Homebrew et pourra figurer dans le manifeste optionnel des outils .NET historiques.

## Migration effectuée sur ce Mac

| Runtime | Version globale | Installation utilisée |
| --- | --- | --- |
| Node | Branche 24, actuellement 24.22.2 | Installation mise existante |
| Python | 3.13.3 | Interpréteur uv ; anciennes installations mise/pyenv conservées sur disque |
| Bun | 1.4.4 | Installation mise |
| Java | Zulu 17.0.15, distribution 17.58.21.0 | JDK existant de SDKMAN importé dans mise |
| Go | 1.25.4 | Installation existante /usr/local/go importée |
| Rust | 1.91.1 | Toolchain rustup existante importée ; autres toolchains conservées |
| Julia | 1.12.6 | Installation Juliaup existante importée |
| Oh My Pi | 18.16.0 | Binaire GitHub géré par mise |

La configuration globale ~/.config/mise/config.toml est une copie gérée par chezmoi depuis home/dot_config/mise/config.toml. Les anciennes installations restent sur disque ; leurs mises à jour futures doivent passer par mise pour éviter de changer une version importée derrière son nom. Une modification faite avec mise use --global doit être récupérée avec chezmoi re-add ~/.config/mise/config.toml.

Les fichiers de projets .nvmrc, .java-version, .sdkmanrc et rust-toolchain.toml sont lus par mise. uv lit .python-version et les contraintes Python du projet. Pour Python, utiliser uv python pin, uv sync et uv run python : la commande python seule hors environnement virtuel conserve le défaut installé par uv --default. Le pin global est ~/.config/uv/.python-version ; la préférence only-managed est dans uv.toml. Mise exclut ses shims python et python3.

Sur une nouvelle machine, mise install télécharge les versions déclarées. Les liens vers les installations historiques de ce Mac ne sont pas nécessaires pour la restauration.

## Sauvegardes et retour arrière

Chezmoi permet de lire le diff avant application et de détecter les modifications externes aux fichiers déjà gérés. Utiliser --less-interactive sur une machine existante, ou --error-on-conflict dans une automatisation. Chezmoi n'est pas une sauvegarde des fichiers personnels : conserver une sauvegarde séparée avant la première application.

La migration des runtimes du Mac dispose de sa propre sauvegarde sous ~/.local/state/mise-runtime-migration/. Elle contient les anciens fichiers shell et la configuration mise précédente. Les installations SDKMAN, Juliaup, pyenv, Go, Bun et rustup restent disponibles.

La migration chezmoi a également sauvegardé le fichier mise et la cible de son ancien lien dans ~/.local/state/chezmoi-migration/. Les configurations mise/uv ont été appliquées avec chezmoi. Des sous-dossiers tools-* et agents-* conservent les anciens exécutables uv/RTK et les configurations des agents avant setup. Les autres fichiers personnels du Mac n'ont pas été remplacés.

## Références

- [Mise : configuration globale et priorités](https://mise.jdx.dev/configuration.html)
- [Mise : import d'une installation existante](https://mise.jdx.dev/cli/link.html)
- [Mise : Rust et fichiers de projets](https://mise.jdx.dev/lang/rust.html)
- [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile)
- [Chezmoi : prise en main](https://www.chezmoi.io/quick-start/)
- [uv : versions Python et pin global](https://docs.astral.sh/uv/concepts/python-versions/)
- [Oh My Pi : installation et plugins](https://github.com/can1357/oh-my-pi)
- [context-mode : installation Codex](https://github.com/mksglu/context-mode/blob/main/docs/install/codex.md)
- [RTK : intégrations des agents](https://github.com/rtk-ai/rtk)
- [Zed : lanceur et option --wait](https://zed.dev/docs/reference/cli)
- [Ghostty : fichiers de configuration](https://ghostty.org/docs/config)
- [Bun : délai minimal avant installation](https://bun.com/docs/runtime/bunfig#installminimumreleaseage)
- [npm : délai minimal en jours](https://docs.npmjs.com/cli/using-npm/config/#min-release-age)
