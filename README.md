# staresc-ng

staresc-ng is based on an internal tool developed by @brn1337 on GitLab. 
This is my attempt to make the penetration tests over ssh great again :)

## Install

```bash
git clone https://gitlab.com/5amu/staresc && cd staresc
sudo make requirements # or without sudo to install just for the user
python3 staresc.py ssh://user:password@target:port/root:rootpw
```

On Arch:

```bash
paru -S staresc
```

## Plugin's naming

It is not mandatory, but it is good to keep track

```
if generic, leave os-name empty:

[os-name]-[identifier].py

# os-name
aix, archlinux, centos, cygwin, debian, freebsd, generic, hp-ux, kali, macos, openbsd, os400, pop, rhel, ubuntu, z/os
```

## Usage

```
usage: staresc [-h] [-v] [-d] [-c C] [-r R] (-f F | connection)

Make SSH/TELNET PTs great again!

positional arguments:
  connection         schema://user:auth@host:port/root_usr:root_passwd
                     auth can be either a password or a path to ssh
                     privkey, specified as \\path\\to\\privkey

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      increase output verbosity (-vv for debug)
  -d, --dontparse    do not parse as soon as the commands are executed
  -c C, --config C   path to plugins directory
  -r R, --results R  results to be parsed (if already existing)
  -f F, --file F     input file: 1 connection string per line
```

## Disclaimer

Needs more testing!! It has to be treated as beta software!!!!
