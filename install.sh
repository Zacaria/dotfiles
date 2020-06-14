EMAIL=havesomecode@gmail.com

# Generate ssh key if not exists
if [ ! -f "~/.ssh/id_rsa.pub" ]; then
  ssh-keygen -t rsa -b 4096 -C "$EMAIL"
fi

# Zsh

brew install zsh
chsh -s /usr/local/bin/zsh

# Oh my zsh

sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
cp .zshrc ~

chmod 755 /usr/local/share/zsh
chmod 755 /usr/local/share/zsh/site-functions

## Theme powerlevel10k
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/themes/powerlevel10k

source ~/.zshrc

p10k configure

# Configure git

git config --global user.name Zacaria
git config --global user.email "$EMAIL"
git config --global push.default simple

# install brew
echo "Installing Brew"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"


# Setup node
echo "Installing node"

brew install n
n lts

# Install yarn
curl -o- -L https://yarnpkg.com/install.sh | bash
