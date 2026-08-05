{ pkgs ? import <nixpkgs> {} }:
let
  tiptapy = _:
    pkgs.python3Packages.buildPythonPackage rec {
      pname = "tiptapy";
      format = "pyproject";
      version = "0.21.0";

      nativeBuildInputs = with pkgs.python3Packages; [
        setuptools
      ];

      propagatedBuildInputs = (with pkgs.python3Packages; [
       jinja2
      ]);

      src = pkgs.fetchPypi {
        inherit pname;
        inherit version;
        hash = "sha256-G5lVXVZe8ULsBRJLrmUt8qA2dK+yUS7pi7JyaTyTq/Y=";
      };
    };
in
pkgs.mkShell {
  packages = with pkgs; [
    (pkgs.python3.withPackages (python-pkgs: with python-pkgs; [
      (pkgs.callPackage tiptapy {})
      flask
      flask-compress
      gunicorn
      psycopg
      psycopg-pool
      requests
    ]))
  ];
}
