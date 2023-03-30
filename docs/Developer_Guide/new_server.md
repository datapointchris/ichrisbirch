# Setup a New Server

## Installs

```bash
# Install ZSH
sudo apt update && sudo apt upgrade
sudo apt install zsh -y
sudo apt install neofetch -y

# Install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Get dotfiles (need access token)
git clone https://github.com/datapointchris/dotfiles.git ~/.dotfiles

# Symlink dotfiles
source ~/.dotfiles/symlinks-ec2

# Install bpytop
sudo apt install bpytop -y
```
