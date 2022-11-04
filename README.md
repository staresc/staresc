<h1 align="center"><img width="300px" src="assets/cover.png" alt="Staresc"></h1>
<h4 align="center">fast and reliable local vulnerability scanner</h4>

</br>

<p align="center">

<a href="https://github.com/5amu/staresc-ng/actions/workflows/release.yml" alt="release">
<img src="https://github.com/5amu/staresc-ng/actions/workflows/release.yml/badge.svg"></a>

<a href="https://github.com/staresc/staresc/actions/workflows/documentation.yml" alt="documentation">
<img src="https://github.com/staresc/staresc/actions/workflows/documentation.yml/badge.svg"></a>

<a href="https://github.com/staresc/staresc/actions/workflows/tests.yml" alt="tests">
<img src="https://github.com/staresc/staresc/actions/workflows/tests.yml/badge.svg"></a>

</p>



Initially developed as an internal tool for [@5amu](https://github.com/5amu)'s day job, thanks to [@cekout](https://github.com/cekout) it became clear that the software could be generalized for a larger audience. So it became public. The project is heavily inspired by [nuclei](https://github.com/projectdiscovery/nuclei), but it targets another audience, such as professionals testing network objects with SSH or Telnet credentials. 

## Usage

```
usage: staresc [-h] [-d] [-nb] [-t TIMEOUT] (-f F | -cs CS | --test | -v) [-o pattern | -of FMT] {scan,raw,check} ...

Make SSH/TELNET PTs great again!
The connection string format is the following: schema://user:auth@host:port
auth can be either a password or a path to ssh privkey, specified as \\path\\to\\privkey

positional arguments:
  {scan,raw,check}      Staresc execution mode
    scan                Scan mode: execute plugins on target
    raw                 Raw mode: execute custom commands
    check               Check mode: check reachability

options:
  -h, --help            show this help message and exit
  -d, --debug           increase output verbosity to debug mode
  -nb, --nobanner       hide banner
  -t TIMEOUT, --timeout TIMEOUT
                        set timeout for connections
  -f F, --file F        input file containing 1 connection string per line
  -cs CS, --connection CS
                        connection string
  --test                test staresc integrity
  -v, --version         print version and exit
  -o pattern, --output pattern
                        export results in specified format
  -of FMT, --output-format FMT
                        format of results
```

## Install

### Using pip

```bash
pip install git+https://github.com/staresc/staresc.git
```

### From the AUR

```bash
paru -S staresc
```

### Compiled version

Download the latest version of the pyinstaller's compiled binary:
[https://github.com/staresc/staresc/releases/latest/](https://github.com/staresc/staresc/releases/latest/)
