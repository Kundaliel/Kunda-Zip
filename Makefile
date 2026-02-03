CC = gcc
CFLAGS = -Wall -Wextra -O3 -std=c11
LDFLAGS = -llzma -lssl -lcrypto

# Auto-detect macOS Homebrew
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    # Try to detect Homebrew prefix
    HOMEBREW_PREFIX := $(shell brew --prefix 2>/dev/null)
    ifneq ($(HOMEBREW_PREFIX),)
        CFLAGS += -I$(HOMEBREW_PREFIX)/include
        LDFLAGS += -L$(HOMEBREW_PREFIX)/lib
    endif
endif

# Manual override: make CUSTOM_PREFIX=/opt/homebrew
ifdef CUSTOM_PREFIX
    CFLAGS += -I$(CUSTOM_PREFIX)/include
    LDFLAGS += -L$(CUSTOM_PREFIX)/lib
endif

TARGET = build/kunda_zip
SRC = src/c/kunda_zip.c

all: check-deps $(TARGET)

# Check for required dependencies
check-deps:
	@echo "Checking dependencies..."
	@command -v $(CC) >/dev/null 2>&1 || { echo "ERROR: gcc not found. Please install gcc."; exit 1; }
	@echo "  ✓ gcc found"
	@pkg-config --exists liblzma 2>/dev/null || { echo "WARNING: liblzma not found via pkg-config"; }
	@pkg-config --exists openssl 2>/dev/null || { echo "WARNING: openssl not found via pkg-config"; }
	@echo "Dependencies check complete."

# Install dependencies (OS-specific)
install-deps:
	@echo "Installing dependencies for your OS..."
ifeq ($(UNAME_S),Darwin)
	@command -v brew >/dev/null 2>&1 || { echo "ERROR: Homebrew not installed. Install from https://brew.sh"; exit 1; }
	brew install xz openssl
	@echo "✓ Dependencies installed via Homebrew"
else ifeq ($(UNAME_S),Linux)
	@if command -v apt-get >/dev/null 2>&1; then \
		echo "Detected Debian/Ubuntu..."; \
		sudo apt-get update && sudo apt-get install -y liblzma-dev libssl-dev gcc make; \
	elif command -v dnf >/dev/null 2>&1; then \
		echo "Detected Fedora/RHEL..."; \
		sudo dnf install -y xz-devel openssl-devel gcc make; \
	elif command -v yum >/dev/null 2>&1; then \
		echo "Detected CentOS/older RHEL..."; \
		sudo yum install -y xz-devel openssl-devel gcc make; \
	elif command -v pacman >/dev/null 2>&1; then \
		echo "Detected Arch Linux..."; \
		sudo pacman -S --needed xz openssl gcc make; \
	else \
		echo "ERROR: Unknown package manager. Please install: liblzma-dev, libssl-dev, gcc, make"; \
		exit 1; \
	fi
	@echo "✓ Dependencies installed"
else
	@echo "ERROR: Unsupported OS. Please manually install: liblzma, openssl, gcc"
	@exit 1
endif

$(TARGET): $(SRC)
	@mkdir -p build
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

debug: CFLAGS = -Wall -Wextra -g -std=c11
debug: $(TARGET)

clean:
	rm -rf build/

install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/

uninstall:
	rm -f /usr/local/bin/$(TARGET)

.PHONY: all check-deps install-deps debug clean install uninstall
