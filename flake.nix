{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    nixpkgs-python.inputs = { nixpkgs.follows = "nixpkgs"; };
  };
  outputs = { self, nixpkgs, devenv, systems, ... } @ inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      packages = forEachSystem (system: {
        devenv-up = self.devShells.${system}.default.config.procfileScript;
      });
      devShells = forEachSystem
        (system:
          let
            pkgs = nixpkgs.legacyPackages.${system};

            pythonPath = pkgs.lib.concatStringsSep ":" [
              "${pkgs.python27Packages.bluepy}/${pkgs.python27.sitePackages}"
              "${pkgs.python27Packages.numpy}/${pkgs.python27.sitePackages}"
              "${pkgs.python27Packages.scipy}/${pkgs.python27.sitePackages}"
              "${pkgs.python27Packages.pandas}/${pkgs.python27.sitePackages}"
              "${pkgs.python27Packages.matplotlib}/${pkgs.python27.sitePackages}"
              "$PYTHONPATH"
            ];
            
            # Define a helper function for running with the right environment
            runWithBt = script: args: ''
              PYTHONPATH="${pythonPath}" sudo -E PYTHONPATH="${pythonPath}" python2 ${builtins.toString ./.}/BadgeFramework/${script} ${args}
            '';
          in
          {
            default = devenv.lib.mkShell {
              inherit inputs pkgs;
              modules = [
                ({ pkgs, lib, config, ... }: {
                  dotenv.disableHint = true;
                  env = {
                    WELCOME_MESSAGE = ''
                      ========================================
                      BadgeFramework Environment Ready
                      Use these commands:
                      • scan - Scan for nearby badges
                      • terminal <MAC_ADDRESS> - Connect to a specific badge
                      • badge-gui - Launch the GUI interface
                      • hub - Run the hub to manage multiple badges
                      ========================================
                    '';
                  };
                  languages.c = {
                    enable = true;
                  };
                  languages.python = {
                    enable = true;
                    version = "2.7.18.8";
                  };
                  packages = with pkgs; [
                    gcc-arm-embedded-13
                    socat
                    picocom
                    glib
                    python27Packages.pip
                    python27Packages.bluepy
                    python27Packages.numpy
                    python27Packages.scipy
                    python27Packages.pandas
                    python27Packages.matplotlib
                    pyocd
                  ];
                  
                  # Scripts for running with bluetooth permissions
                  scripts = {
                    scan = {
                      exec = runWithBt "scan_all.py" "";
                      description = "Scan for nearby badges";
                    };
                    
                    terminal = {
                      exec = runWithBt "terminal.py" "$@";
                      description = "Connect to a specific badge: terminal <MAC_ADDRESS>";
                    };
                    
                    badge-gui = {
                      exec = runWithBt "badge_gui.py" "";
                      description = "Launch the GUI interface";
                    };
                    
                    hub = {
                      exec = runWithBt "hub_V1.py" "";
                      description = "Run the hub to manage multiple badges";
                    };
                    
                    # Helper to run any Python script with BT permissions
                    run-with-bt = {
                      exec = ''
                        PYTHONPATH="${pythonPath}" sudo -E PYTHONPATH="${pythonPath}" python2 "$@"
                      '';
                      description = "Run any Python script with Bluetooth permissions";
                    };
                  };
                  
                  # Print welcome message on shell entry
                  enterShell = ''
                    echo "$WELCOME_MESSAGE"
                  '';
                })
              ];
            };
          });
    };
}
