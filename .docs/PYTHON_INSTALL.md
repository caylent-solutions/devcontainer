# Python Installation Guide

## For macOS (Using asdf)

1. First, clone asdf into your home directory:
```bash
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.13.1
```

2. Add asdf to your shell configuration:

For zsh (recommended, default shell on modern macOS), add to `~/.zshrc`:
```bash
echo '. "$HOME/.asdf/asdf.sh"' >> ~/.zshrc
echo '. "$HOME/.asdf/completions/asdf.bash"' >> ~/.zshrc
```

For bash, add to `~/.bashrc` (Linux) or `~/.bash_profile` (macOS):
```bash
echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc  # or ~/.bash_profile for macOS
echo '. "$HOME/.asdf/completions/asdf.bash"' >> ~/.bashrc  # or ~/.bash_profile for macOS
```

Note: We recommend using zsh as it's the default shell in modern macOS and provides better features and plugin support.

3. Restart your shell or source the configuration:
```bash
source ~/.zshrc
```

4. Install the Python plugin for asdf:
```bash
asdf plugin add python
```

5. Install Python 3.12.9:
```bash
asdf install python 3.12.9
```

6. Set Python 3.12.9 as your global version:
```bash
asdf global python 3.12.9
```

7. Reshim asdf to ensure Python 3.12.9 is available in your current shell:
```bash
asdf reshim
```

8. Verify the installation:
```bash
python --version  # Should show 3.12.9
```

## For Windows (Using Windows Store or Official Installer)

1. **Option 1: Windows Store (Recommended)**
   - Open the Microsoft Store
   - Search for "Python 3.12"
   - Click "Get" or "Install" for Python 3.12
   - Follow the installation prompts

2. **Option 2: Official Python Installer**
   - Visit [Python Downloads](https://www.python.org/downloads/)
   - Download Python 3.12.9 installer for Windows
   - Run the installer
   - **Important**: Check "Add Python 3.12 to PATH" during installation
   - Click "Install Now"

3. Verify the installation:
   - Open Command Prompt or PowerShell
   - Run:
   ```bash
   python --version  # Should show 3.12.9
   ```

## Verification

After installing Python on either platform, you can verify it's working correctly by running:
```bash
python --version
pip --version
```

Both commands should execute successfully and show version numbers.