{
  description = "Midi Fighter 3D Macro Controller - Stream deck, soundboard, and automation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python packages we need
        pythonPackages = pkgs.python313Packages;
        
        # Create a Python environment with all our dependencies
        pythonEnv = pkgs.python313.withPackages (ps: with ps; [
          # Core dependencies from pyproject.toml
          mido
          python-rtmidi
          pyyaml
          sounddevice
          soundfile
          numpy
          httpx
          pynput
          
          # Development tools
          mypy
        ]);
        
      in {
        # Development shell
        devShells.default = pkgs.mkShell {
          name = "midi-macro-dev";
          
          buildInputs = with pkgs; [
            # Our Python environment with all packages
            pythonEnv
            
            # System libraries needed at runtime
            alsa-lib
            portaudio
            
            # Build tools (just in case)
            gcc
            gnumake
            pkg-config
            
            # Development tools
            uv  # Keep uv for project management (not for package installation)
          ];
          
          shellHook = ''
            echo "🎹 Midi Fighter 3D Macro Controller"
            echo ""
            echo "Python packages available:"
            python --version
            echo "  - mido (MIDI I/O)"
            echo "  - python-rtmidi (MIDI backend)"
            echo "  - sounddevice + soundfile (audio)"
            echo "  - numpy (audio processing)"
            echo "  - pynput (keyboard automation)"
            echo "  - httpx (webhooks)"
            echo "  - mypy (type checking)"
            echo ""
            echo "Available commands:"
            echo "  python src/main.py     - Run the application"
            echo "  python test_mf3d.py    - Test MIDI connectivity"
            echo "  mypy src/              - Type check the code"
            echo ""
            
            # Set library path for audio
            export LD_LIBRARY_PATH="${pkgs.alsa-lib}/lib:${pkgs.portaudio}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
          '';
        };
        
        # Package for installation
        packages.default = pkgs.stdenv.mkDerivation {
          name = "midi-macro";
          version = "0.1.0";
          src = ./.;
          
          buildInputs = [ pythonEnv ];
          
          installPhase = ''
            mkdir -p $out/bin
            mkdir -p $out/share/midi-macro
            
            # Copy source files
            cp -r src $out/share/midi-macro/
            cp -r config $out/share/midi-macro/
            
            # Create wrapper script
            cat > $out/bin/midi-macro << 'EOF'
            #!/usr/bin/env bash
            cd $out/share/midi-macro
            exec python src/main.py "$@"
            EOF
            chmod +x $out/bin/midi-macro
          '';
        };
        
        # App for running with 'nix run'
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/midi-macro";
        };
      });
}
