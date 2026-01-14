# NIX configuration for Replit
{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.libjpeg
    pkgs.zlib
    pkgs.libpng
  ];
}
