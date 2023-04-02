# Setup a New Server

## TODO: This all needs updating

## Installs

```bash
# Install ZSH
sudo apt update && sudo apt upgrade
sudo apt install zsh -y
sudo apt install neofetch -y
# Install from apt-list here

# Install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Get dotfiles (need access token)
git clone https://github.com/datapointchris/dotfiles.git ~/code/dotfiles

# Symlink dotfiles
# TODO: [2023/04/01] - Update this
source ~/.dotfiles/symlinks-ec2

```
