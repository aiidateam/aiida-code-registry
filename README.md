# AiiDA code registry

**THIS IS WORK IN PROGRESS - PULL REQUESTS & [SUGGESTIONS](https://github.com/aiidateam/aiida-code-registry/issues) HIGHLY WELCOME**

This repository collects configurations of simulation codes on public compute resources for direct setup in AiiDA.

## Importing computers into AiiDA

```
verdi computer setup --config https:///..../computer-setup.yml
```

Some computers also require specific configuration options and provide a specific `computer-configure.yml` file:

```
verdi computer configure ssh <computer-name> --config https:///..../computer-configure.yml
```

Note: Some computers may need to be accessed via a proxy - e.g., for Piz Daint: 
```
proxy_command: ssh <username>@ela.cscs.ch netcat daint.cscs.ch 22
```

## Importing codes into AiiDA
```
verdi code setup --config https://.../code.yml
```

## Contributing to this repository

We highly appreciate help in keeping the configurations up to date and adding new simulation codes & computers.

 1. Fork this repository
 2. Add your computer / code
 3. Create a Pull Request
