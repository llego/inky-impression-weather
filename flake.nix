{
  description = "Inky Impression weather display";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python313.withPackages (ps: [
            ps.pillow
            ps.requests
          ]);
        in {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.ruff
            ];
          };
        });
    };
}
