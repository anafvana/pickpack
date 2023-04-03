# `pickpack` for devs

If you are thinking of cloning or modifying `pickpack`, here are some tips, divided into the following sections:

<!-- TOC start -->

- [`poetry`](#poetry)
  - [Installing `poetry`](#installing-poetry)
  - [Installing dependencies](#installing-dependencies)
  - [Updating dependencies](#updating-dependencies)
- [`ci`](#ci)
- [Distributing on PyPi](#distributing-on-pypi)
  - [`twine`](#twine)
- [Testing](#testing)
<!-- TOC end -->

## `poetry`

`pickpack` has been packaged using `poetry`

### Installing `poetry`

You can either install `poetry` through your distribution's package manager or with

```
curl -sSL https://install.python-poetry.org | python3 -
```

Beware: `poetry` lock files are not always backwards compatible. Current lock files (`poetry 1.4`) are not compatible with `poetry 1.2`.

### Installing dependencies

Once you have `poetry`, you can run the following command to install dependencies:

```
poetry install
```

If you want to also install dependencies from a specific group (for example, `dev`), use:

```
poetry install --with dev
```

### Updating dependencies

When adding new dependencies or updating existing ones in your `pyproject.toml`, remember to update the lock file with

```
poetry lock
```

If you want to avoid upgrading dependencies, you may run

```
poetry lock --no-update
```

## `ci`

If you want to continue using the CI pipeline under `.github/workflows/ci.yml`, you will need to take a few elements into account:

1. Python version: what versions will your fork support?
2. OSs, especially Ubuntu LTS: what versions will you test with?
   - From experience, testing with a very old version of Ubuntu may lead to fails simply because the image has become unavailable
3. `poetry` version: as previously said, `poetry` lock files are not always backwards compatible. Make sure you are running `poetry` commands with a compatible version of the package.

## Distributing on PyPi

There are different ways to distribute packages on PyPi. For `pickpack`, `twine` has been used. This one is up to you.

To bundle your package and get it ready for upload:

```
poetry build
```

### `twine`

If you choose to use `twine`, you can install it with

```
pip install twine
```

Then, set up your credentials in `$HOME/.pypirc':

```
[pypi]
	username = __token__
	password = <token generated on PyPi>
```

Finally, upload your package with

```
twine upload -r pypi path/to/package/dist/*
```

## Testing

You can either write a script which runs whatever tests you want on its own or alter the tests already specified under `tests/test_pickpack.py`.

To run the aforementioned file using `poetry`, use the command:

```
poetry run python tests/test_pickpack.py
```
