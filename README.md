<h1 align="center"><img width="300px" src="assets/cover.png" alt="Staresc"></h1>
<h4 align="center">automatic and extendable vulnerability assessment over SSH</h4>

Initially developed as an internal tool for [@5amu](https://github.com/5amu)'s day job, thanks to [@cekout](https://github.com/cekout) it became clear that the software could be generalized for a larger audience. So it became public. The project is heavily inspired by [nuclei](https://github.com/projectdiscovery/nuclei), but it targets another audience, such as professionals testing network objects with SSH or Telnet credentials. 

## Usage

```usage: staresc [-h] [-d] [-c C] [-ocsv filename] [-oxlsx filename] [-ojson filename] [-oall pattern] [-t] [-v] [-f F] [--test-plugins] [connection]

Make SSH/TELNET PTs great again!

positional arguments:
  connection            schema://user:auth@host:port/root_usr:root_passwd
                        auth can be either a password or a path to ssh
                        privkey, specified as \\path\\to\\privkey

options:
  -h, --help            show this help message and exit
  -d, --debug           increase output verbosity to debug mode
  -c C, --config C      path to plugins directory
  -oall pattern, --output-all pattern
                        export results in all possible formats
  -t, --test            test staresc integrity
  -v, --version         print version and exit
  -f F, --file F        input file: 1 connection string per line
  --test-plugins        test the specified plugins

  -ocsv filename, --output-csv filename
                        export results on a csv file
  -oxlsx filename, --output-xlsx filename
                        export results on a xlsx (MS Excel) file
  -ojson filename, --output-json filename
                        export results on a json file
```
