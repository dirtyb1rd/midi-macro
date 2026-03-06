{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # Build tools go in nativeBuildInputs so they're in PATH
  nativeBuildInputs = with pkgs; [
    gcc
    gnumake
    ninja  # Required for python-rtmidi build (meson-python)
    pkg-config  # For detecting system libraries
    python313
    uv
  ];
  
  # Libraries and runtime deps go in buildInputs
  buildInputs = with pkgs; [
    # System libraries for audio and MIDI
    alsa-lib
    portaudio
    
    # Kernel headers for evdev (pynput dependency)
    linuxHeaders
  ];
  
  # Set up environment for building Python packages with C extensions
  shellHook = ''
    echo "Setting up build environment for midi-macro..."
    
    # Add ninja to PATH explicitly (needed for uv's build isolation)
    export PATH="${pkgs.ninja}/bin:$PATH"
    
    # Verify tools are available
    echo "Checking build tools..."
    which ninja && echo "✓ ninja found: $(ninja --version)"
    which gcc && echo "✓ gcc found"
    which pkg-config && echo "✓ pkg-config found"
    
    # Export kernel headers location for evdev build
    export C_INCLUDE_PATH="${pkgs.linuxHeaders}/include''${C_INCLUDE_PATH:+:$C_INCLUDE_PATH}"
    export CFLAGS="-I${pkgs.linuxHeaders}/include"
    
    # Also set PKG_CONFIG_PATH for libraries
    export PKG_CONFIG_PATH="${pkgs.alsa-lib}/lib/pkgconfig:${pkgs.portaudio}/lib/pkgconfig''${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
    
    # Set library path for runtime
    export LD_LIBRARY_PATH="${pkgs.alsa-lib}/lib:${pkgs.portaudio}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    
    echo ""
    echo "Environment ready! Run: uv sync"
  '';
}
