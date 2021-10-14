# AiiDA code registry

**THIS IS WORK IN PROGRESS - PULL REQUESTS & [SUGGESTIONS](https://github.com/aiidateam/aiida-code-registry/issues) HIGHLY WELCOME**

This repository collects configurations of simulation codes on public compute resources for quick and easy setup in AiiDA.

## Using the AiiDA code registry

In the following we'll take the example of [Piz Daint](https://www.cscs.ch/computers/piz-daint/), a HPC system at the Swiss National Supercomputing Centre.

### `verdi computer setup` 

 1. Navigate to the [`daint.cscs.ch`](./daint.cscs.ch) folder in the GitHub web interface
 2. Select the partition you would like to run on, for example [`hybrid`](./daint.cscs.ch/hybrid)
 3. Click on the `computer-setup.yaml` file and click on the "Raw" button to get a direct link to the file

Now use this link to set up the computer directly via the `verdi` command line:
```
verdi computer setup --config https://raw.githubusercontent.com/aiidateam/aiida-code-registry/master/daint.cscs.ch/hybrid/computer-setup.yaml
```

Note: Alternatively, you can first create a local clone of the `aiida-code-registry` and set up the computer from there.
This allows you to edit the configuration files in case you need to adapt anything.

### `verdi computer configure` 

Some computers require specific configuration options (e.g. to jump over a login node) and provide a dedicated `computer-configure.yaml` file.

You'll find it in the same folder:

```
verdi computer configure ssh daint-hybrid --config https://raw.githubusercontent.com/aiidateam/aiida-code-registry/master/daint.cscs.ch/hybrid/computer-configure.yaml
```

At this point, you should be able to successfully run:
```
verdi computer test daint-hybrid
```

### `verdi code setup` 

The [`daint.cscs.ch`](./daint.cscs.ch/) folder contains a [`codes`](./daint.cscs.ch/codes) subfolder with configuration files for individual codes.

Just pick the ones you need and set them up:

```
verdi code setup --config https://raw.githubusercontent.com/aiidateam/aiida-code-registry/master/daint.cscs.ch/codes/cp2k-8.1-hybrid.yaml
```

## Contributing to this repository

We highly appreciate help in keeping the configurations up to date and adding new simulation codes & computers.

 1. Fork this repository
 2. Add your computer / code
 3. Create a Pull Request
