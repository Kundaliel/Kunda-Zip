#!/bin/bash

# Kunda Zip GitHub Setup Script
# This script initializes a git repository, creates organized commits, and pushes to GitHub

set -e  # Exit on error

echo "======================================"
echo "Kunda Zip - GitHub Repository Setup"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed. Please install git first.${NC}"
    exit 1
fi

# Get GitHub repository URL from user
echo -e "${BLUE}Enter your GitHub repository URL (e.g., https://github.com/username/kunda-zip.git):${NC}"
read -r REPO_URL

if [ -z "$REPO_URL" ]; then
    echo -e "${RED}Error: Repository URL cannot be empty${NC}"
    exit 1
fi

# Get user info for commits
echo ""
echo -e "${BLUE}Enter your name for git commits:${NC}"
read -r GIT_NAME

echo -e "${BLUE}Enter your email for git commits:${NC}"
read -r GIT_EMAIL

if [ -z "$GIT_NAME" ] || [ -z "$GIT_EMAIL" ]; then
    echo -e "${RED}Error: Name and email are required${NC}"
    exit 1
fi

# Check if .git exists
if [ -d ".git" ]; then
    echo -e "${YELLOW}Warning: Git repository already exists in this directory${NC}"
    echo "Do you want to remove it and start fresh? (y/n)"
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        rm -rf .git
        echo -e "${GREEN}Removed existing git repository${NC}"
    else
        echo -e "${YELLOW}Keeping existing repository. Will add new commits.${NC}"
    fi
fi

# Initialize git repository if needed
if [ ! -d ".git" ]; then
    echo -e "${GREEN}Initializing git repository...${NC}"
    git init
fi

# Configure git
echo ""
echo -e "${GREEN}Configuring git...${NC}"
git config user.name "$GIT_NAME"
git config user.email "$GIT_EMAIL"

# Create .gitignore
echo -e "${GREEN}Creating .gitignore...${NC}"
cat > .gitignore << 'EOF'
# Build artifacts
build/
*.o
*.a
*.so
*.dylib

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
env/
ENV/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Test files
test_files/
*.kun
extracted/

# Logs
*.log
EOF

# Stage and commit .gitignore first
git add .gitignore
git commit -m "Initial commit: Add .gitignore" || true

# Commit project structure
echo -e "${GREEN}Committing project documentation...${NC}"
git add README.md
git commit -m "docs: Add comprehensive README with usage instructions" || true

# Commit build system
echo -e "${GREEN}Committing build system...${NC}"
git add Makefile setup.sh
git commit -m "build: Add Makefile and automated setup script

- Makefile with multiple build targets
- Auto-detection of dependencies
- Support for macOS and Linux
- Debug and release builds" || true

# Commit C implementation
echo -e "${GREEN}Committing C implementation...${NC}"
git add src/c/
git commit -m "feat: Add high-performance C implementation

- Ultra LZMA compression with up to 1.5GB dictionary
- Path compression for efficient metadata
- File type detection
- SHA-256 checksum support
- Multiple compression presets" || true

# Commit Python implementations
echo -e "${GREEN}Committing Python implementations...${NC}"
git add src/python/kunda.py
git commit -m "feat: Add original Python implementation

- Basic LZMA compression
- Cross-platform compatibility
- Easy to modify and extend" || true

git add src/python/kunda_ultra.py
git commit -m "feat: Add optimized Python implementation

- Enhanced performance
- Better error handling
- Improved compression parameters" || true

# Commit GUI if it exists
if [ -f "src/python/kunda_gui_tk.py" ]; then
    git add src/python/kunda_gui_tk.py
    git commit -m "feat: Add GUI version with Tkinter

- User-friendly graphical interface
- Drag-and-drop support
- Visual progress indicators" || true
fi

# Create docs directory structure
echo -e "${GREEN}Setting up documentation structure...${NC}"
mkdir -p docs

# Create a simple index.html for GitHub Pages
cat > docs/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kunda Zip - Multi-Platform Archiver</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f6f8fa;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        h1 { margin: 0; font-size: 2.5em; }
        .subtitle { opacity: 0.9; margin-top: 10px; }
        .content {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .feature {
            margin: 20px 0;
            padding: 15px;
            background: #f6f8fa;
            border-left: 4px solid #667eea;
        }
        code {
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        .button {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 10px 10px 0;
        }
        .button:hover { background: #764ba2; }
    </style>
</head>
<body>
    <header>
        <h1>🗜️ Kunda Zip</h1>
        <p class="subtitle">High-Performance Multi-Platform File Archiver</p>
    </header>
    
    <div class="content">
        <h2>Features</h2>
        <div class="feature">
            <strong>🚀 Ultra LZMA Compression</strong><br>
            Up to 1.5 GB dictionary size for maximum compression ratios
        </div>
        <div class="feature">
            <strong>📁 Path Compression</strong><br>
            Intelligent deduplication of common directory prefixes
        </div>
        <div class="feature">
            <strong>🔍 File Type Detection</strong><br>
            Automatically optimizes compression for different file types
        </div>
        <div class="feature">
            <strong>✅ SHA-256 Checksums</strong><br>
            Optional integrity verification for peace of mind
        </div>
        
        <h2>Quick Start</h2>
        <p>Compress a file or directory:</p>
        <code>./build/kunda_zip create myfile.txt output.kun ultra</code>
        
        <p style="margin-top: 15px;">Extract an archive:</p>
        <code>./build/kunda_zip extract output.kun</code>
        
        <h2>Get Started</h2>
        <a href="https://github.com/yourusername/kunda-zip" class="button">View on GitHub</a>
        <a href="https://github.com/yourusername/kunda-zip/releases" class="button">Download</a>
        
        <h2>Available Implementations</h2>
        <ul>
            <li><strong>C Version:</strong> 5-10x faster, lowest memory usage, best for production</li>
            <li><strong>Python Version:</strong> Cross-platform, easy to modify, no compilation needed</li>
            <li><strong>GUI Version:</strong> User-friendly interface for those who prefer graphical tools</li>
        </ul>
    </div>
</body>
</html>
EOF

git add docs/
git commit -m "docs: Add GitHub Pages site" || true

# Final commit for any remaining files
git add .
git commit -m "chore: Add remaining project files" || true

# Set main branch
echo -e "${GREEN}Setting default branch to main...${NC}"
git branch -M main

# Add remote
echo -e "${GREEN}Adding remote repository...${NC}"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

# Push to GitHub
echo ""
echo -e "${YELLOW}Ready to push to GitHub!${NC}"
echo -e "${BLUE}This will push all commits to: ${REPO_URL}${NC}"
echo ""
echo "Do you want to proceed? (y/n)"
read -r response

if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
    echo -e "${GREEN}Pushing to GitHub...${NC}"
    git push -u origin main
    
    echo ""
    echo -e "${GREEN}======================================"
    echo "✅ Successfully pushed to GitHub!"
    echo "======================================${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Go to your repository settings on GitHub"
    echo "2. Navigate to Pages section"
    echo "3. Set source to 'main' branch and '/docs' folder"
    echo "4. Your site will be available at: https://yourusername.github.io/kunda-zip/"
    echo ""
    echo -e "${YELLOW}Repository URL: ${REPO_URL}${NC}"
else
    echo -e "${YELLOW}Push cancelled. You can push manually later with:${NC}"
    echo "git push -u origin main"
fi

echo ""
echo -e "${GREEN}All done! 🎉${NC}"