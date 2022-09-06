# Spliced Experiment Runs

Hoping we can do a subset of runs on here using the Docker experiment container!
See the [splice-experiment](https://github.com/buildsi/spliced-experiment) repository for details,
and the [.github/analysis.yaml](.github/analysis.yaml) for how the automation works,
and [here](https://github.com/buildsi/smeagle-examples) for the actions.

## Symbols

For runs with symbols it was a simple case of building a library with spack, 
and then comparing across versions. Spliced can do this internally with a spack
splice, but instead we really want to do the same procedure as with two different
libs and install the libs separately and provide the paths. Here is how to do that.
Clone spack:

```bash
$ git clone git@github.com:spack/spack
```

On the host ensure debug flags are on and install across versions of
a spack library.

```bash
$ export SPACK_DEBUG_FLAGS=true
$ spack compiler find
```
This develop branch doesn't have an option to list without the extra, so
we do:

```bash
for package in binutils; do
    for version in $(spack versions --safe ${package}); do
       printf "Installing ${package}@${version}\n"
       spack install ${package}@${version}
    done
done
```

Now we can shell into the container (with the [test_libs_manual.py](test_libs_manual.py)
in your PWD and test for the pattern. Since I wound up running this locally I used docker,
but you could pull a Singularity container instead.

```bash
$ mkdir -p results/manual/binutils
$ docker run -it -v $PWD:/runs -v /home/vanessa/Desktop/Code/spack-vsoch:/spack ghcr.io/buildsi/splice-experiment:ubuntu-20.04 
```

Then run the script. I targeted the exact spack compiler directory I wanted to ensure
staying in the same compiler version/space.

```bash
$ python /runs/test_libs_manual.py /spack/opt/spack/linux-ubuntu20.04-skylake/gcc-9.4.0 binutils --outdir /runs/results/manual/binutils
```

That will save results (json files) to the directory you created. We will add them to
[https://github.com/buildsi/splice-experiment-results](https://github.com/buildsi/splice-experiment-results)
