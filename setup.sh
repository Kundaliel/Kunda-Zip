#!/bin/bash
# Kunda Zip - Universal Setup Script
# Works on macOS, Linux (Ubuntu, Fedora, Arch, etc.)

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Kunda Zip - Automated Setup                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="Windows"
else
    OS="Unknown"
fi

echo "🖥️  Detected OS: $OS"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install dependencies based on OS
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    if [[ "$OS" == "macOS" ]]; then
        # macOS with Homebrew
        if ! command_exists brew; then
            echo "❌ Homebrew not found!"
            echo "Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        
        echo "  Installing via Homebrew..."
        brew install xz openssl gcc make
        echo "  ✓ Dependencies installed"
        
    elif [[ "$OS" == "Linux" ]]; then
        # Linux - detect package manager
        if command_exists apt-get; then
            echo "  Detected Debian/Ubuntu..."
            sudo apt-get update
            sudo apt-get install -y liblzma-dev libssl-dev gcc make pkg-config
            echo "  ✓ Dependencies installed"
            
        elif command_exists dnf; then
            echo "  Detected Fedora/RHEL..."
            sudo dnf install -y xz-devel openssl-devel gcc make pkgconfig
            echo "  ✓ Dependencies installed"
            
        elif command_exists yum; then
            echo "  Detected CentOS/older RHEL..."
            sudo yum install -y xz-devel openssl-devel gcc make pkgconfig
            echo "  ✓ Dependencies installed"
            
        elif command_exists pacman; then
            echo "  Detected Arch Linux..."
            sudo pacman -S --needed --noconfirm xz openssl gcc make pkgconf
            echo "  ✓ Dependencies installed"
            
        elif command_exists apk; then
            echo "  Detected Alpine Linux..."
            sudo apk add --no-cache xz-dev openssl-dev gcc make musl-dev pkgconfig
            echo "  ✓ Dependencies installed"
            
        else
            echo "❌ Unknown package manager!"
            echo "Please manually install: liblzma-dev, libssl-dev, gcc, make"
            exit 1
        fi
        
    elif [[ "$OS" == "Windows" ]]; then
        echo "❌ Windows native builds not supported yet."
        echo "Please use WSL (Windows Subsystem for Linux) or MSYS2."
        exit 1
        
    else
        echo "❌ Unsupported OS: $OS"
        exit 1
    fi
}

# Check if dependencies are already installed
check_dependencies() {
    echo "🔍 Checking for required dependencies..."
    
    MISSING_DEPS=()
    
    if ! command_exists gcc; then
        MISSING_DEPS+=("gcc")
    fi
    
    if ! command_exists make; then
        MISSING_DEPS+=("make")
    fi
    
    # Check for libraries (this is approximate)
    if [[ "$OS" == "macOS" ]]; then
        if ! brew list xz &>/dev/null; then
            MISSING_DEPS+=("xz")
        fi
        if ! brew list openssl &>/dev/null; then
            MISSING_DEPS+=("openssl")
        fi
    elif [[ "$OS" == "Linux" ]]; then
        if ! ldconfig -p | grep -q liblzma; then
            MISSING_DEPS+=("liblzma")
        fi
        if ! ldconfig -p | grep -q libssl; then
            MISSING_DEPS+=("libssl")
        fi
    fi
    
    if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
        echo "  ✓ All dependencies already installed"
        return 0
    else
        echo "  ⚠️  Missing: ${MISSING_DEPS[*]}"
        return 1
    fi
}

# Build the project
build_project() {
    echo ""
    echo "🔨 Building Kunda Zip..."
    
    if [[ "$OS" == "macOS" ]] && command_exists brew; then
        # Use Homebrew prefix on macOS
        make CUSTOM_PREFIX=$(brew --prefix)
    else
        make
    fi
    
    echo "  ✓ Build successful"
}

# Main setup flow
main() {
    # Check dependencies first
    if ! check_dependencies; then
        echo ""
        read -p "Install missing dependencies? [Y/n] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            install_dependencies
        else
            echo "❌ Cannot continue without dependencies."
            exit 1
        fi
    fi
    
    # Build
    build_project
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                   ✓ Setup Complete!                        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Kunda Zip is ready to use:"
    echo "  ./build/kunda_zip create myfile.txt output.kun ultra"
    echo "  ./build/kunda_zip extract output.kun extracted/"
    echo ""
    echo "Or use Python version:"
    echo "  python src/python/kunda.py create myfile.txt output.kun ultra"
    echo ""
    echo "Optional: Install C version system-wide with:"
    echo "  sudo make install"
    echo ""
}

# Run main
main
