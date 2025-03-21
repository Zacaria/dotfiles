EMAIL=havesomecode@gmail.com

# Generate ssh key if not exists
if [ ! -f "~/.ssh/id_rsa.pub" ]; then
  ssh-keygen -t rsa -b 4096 -C "$EMAIL"
fi

# install brew
echo "Installing Brew"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# install git
brew install git

# Zsh

brew install zsh
chsh -s /usr/local/bin/zsh

# Oh my zsh

sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
cp .zshrc ~

chmod 755 /usr/local/share/zsh
chmod 755 /usr/local/share/zsh/site-functions

# ## Theme powerlevel10k
# git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/themes/powerlevel10k

# exec zsh

# p10k configure

# Install Starship
curl -sS https://starship.rs/install.sh | sh

echo "eval \"\$(starship init zsh)\"" >> ~/.zshrc

mkdir -p ~/.config && cp starship.toml ~/.config/starship.toml

# Configure git

git config --global user.name Zacaria
git config --global user.email "$EMAIL"
git config --global push.default simple
git config --global core.editor vim
cp .gitignore_global ~
git config --global core.excludefile ~/.gitignore_global

# Setup node
echo "Installing node"

curl -L https://git.io/n-install | bash -s -- -y
exec zsh
node -v

# Install yarn
curl -o- -L https://yarnpkg.com/install.sh | bash

# Install powerline fonts
git clone https://github.com/powerline/fonts.git --depth=1
cd fonts
./install.sh
cd ..
rm -rf fonts

# Configure screenshots location
mkdir ~/Screenshots
defaults write com.apple.screencapture location ~/Screenshots
killall SystemUIServer

# Install uv for python
curl -LsSf https://astral.sh/uv/install.sh | sh
