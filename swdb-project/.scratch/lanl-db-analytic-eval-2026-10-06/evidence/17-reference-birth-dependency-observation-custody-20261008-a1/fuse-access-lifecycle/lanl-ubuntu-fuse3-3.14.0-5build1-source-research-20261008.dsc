-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

Format: 3.0 (quilt)
Source: fuse3
Binary: fuse3, libfuse3-3, libfuse3-dev, fuse3-udeb, libfuse3-3-udeb
Architecture: linux-any kfreebsd-any
Version: 3.14.0-5build1
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Homepage: https://github.com/libfuse/libfuse/wiki
Standards-Version: 4.6.1
Build-Depends: debhelper-compat (= 13), pkgconf, meson, systemd-dev, python3 <!nocheck>, python3-pytest <!nocheck>
Package-List:
 fuse3 deb utils optional arch=linux-any
 fuse3-udeb udeb debian-installer optional arch=linux-any
 libfuse3-3 deb libs optional arch=linux-any,kfreebsd-any
 libfuse3-3-udeb udeb debian-installer optional arch=linux-any,kfreebsd-any profile=!noudeb
 libfuse3-dev deb libdevel optional arch=linux-any,kfreebsd-any
Checksums-Sha1:
 3820905cd399fe9350285e76e72ceace656a761f 4351852 fuse3_3.14.0.orig.tar.xz
 8addaabc30aa4b6a86f580248ae31e9788d8918c 1012 fuse3_3.14.0.orig.tar.xz.asc
 68744b2523bcb731b3e66cb20c29536cd6353904 17976 fuse3_3.14.0-5build1.debian.tar.xz
Checksums-Sha256:
 96115b2a8ff34bd1e0c7b00c5dfd8297571d7e165042b94498c9a26356a9a70a 4351852 fuse3_3.14.0.orig.tar.xz
 246ae20731da98c5f5a5cf6cdf8d10aa54ea986b4e71fe24805154b186ad30d0 1012 fuse3_3.14.0.orig.tar.xz.asc
 9d1ca42ee3d8d0b8f8ce84f1d032632a20c0a1ef9e1d8837fbcc9e10301fe318 17976 fuse3_3.14.0-5build1.debian.tar.xz
Files:
 2070c0f347e2304fa122d4cb0746e8a9 4351852 fuse3_3.14.0.orig.tar.xz
 c43df823d18a5749c9f1f5890c2438ea 1012 fuse3_3.14.0.orig.tar.xz.asc
 48565e0d026d671553f07db20334e8d2 17976 fuse3_3.14.0-5build1.debian.tar.xz
Original-Maintainer: Laszlo Boszormenyi (GCS) <gcs@debian.org>

-----BEGIN PGP SIGNATURE-----

iQJHBAEBCgAxFiEET7WIqEwt3nmnTHeHb6RY3R2wP3EFAmYUFDcTHGp1bGlhbmtA
dWJ1bnR1LmNvbQAKCRBvpFjdHbA/cbC6D/4p+Pti3fuEaFFjj5x+nbzuBrCRRwnK
RjZ60xGbn0QmO2py9qeKwQf+4Bh1cjy004g5mFF2hE0ZpOYH7ogt3suyzvsPh3Nk
/eBQEZzHHGT6FEiNzETiu5NknGL6qEooqau7s9QuBKxUUgVVmDFVe3dAtBXsguqn
D0d+fUB0q3/LOT6UKTAebikaNxh3IzQA8DkfEBGJ+Xega97Vrr78RwzDDAUBOo98
0PYwka7Ryk6d4Red3EnXkM70NURf3Mmo7+J3o2RByExxjs9bLC9X3fM4k2NWz1Gc
dWf+rkL5X/Sv38w+Qu4s+KKXyIZELaor8+rlOnQLT661/XK30lwFpE4J9xDyAtAZ
OI3YSTSycRKhgssD7i9Bq1b3dBBney1K9+XVarscgNAI4PriY4CT4efFTC7zpsXB
MDqJc2eMDuUWdA2v/98Bc0in8mNifsJ8a9KpkGVS2D1wPSrN/3IF6/50kQpP3geZ
/C/d5SJVcPIf/KjXMM4mTRb/1u4uYSPKNCfIrzwI+Q5AxIsuS/fyz3p7+//Lzscw
QDiLdF0IWkU5jSsP7Sl/A8AfuB2gFDcZSuFcYbRCWLAc+vNEU1/Aadad79Iuv33A
Fer7S34wx5QHySPYXMy0+EPqf3tGLxpDBgqsbJtz9VzFLKVgrp+Da/cZmD3xon34
3lssD67LmN4fXw==
=8K/J
-----END PGP SIGNATURE-----
