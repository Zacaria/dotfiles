EMAIL=havesomecode@gmail.com

# Generate ssh keu if not exists
if [ ! -f "~/.ssh/id_rsa.pub" ]; then
  ssh-keygen -t rsa -b 4096 -C "$EMAIL"
fi

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
