{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
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
          in
          {
            default = devenv.lib.mkShell {
              inherit inputs pkgs;
              modules = [
                ({ pkgs, lib, config, ... }: {
                  dotenv.disableHint = true;

                  env = {
                  };

                  languages.c = {
                    enable = true;
                  };

                  languages.python = {
                    enable = true;
                    venv.enable = true;
                  };

                  packages = with pkgs; [
                    gcc-arm-embedded-13
                    socat
                    picocom
                    glib
                    virtualenv
                    python312Packages.tkinter
                    python312Packages.ipython
                    python312Packages.pandas
                    pyocd
                  ];
                })
              ];
            };
          });
    };
}
