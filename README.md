# AiiDA code registry

This repository collects configurations of simulation codes and computers for direct setup in AiiDA.

## Importing computers into AiiDA

```
verdi computer setup --config https:///..../mycomputer.yml
verdi computer configure ssh mycomputer
```

## Importing codes into AiiDA
```
verdi code setup --config https://.../code.yml
```

## Contributing to this repository

We highly appreciate help in keeping the configurations up to date and adding new simulation codes & computers.

 1. Fork this repository
 2. Add your computer / code
 3. Create a [Pull Request]
