# Developers tips

If github pages fails because external links are broken, add the pages or regex at the end of the ```conf.py``` file
See [this](https://github.com/neuroinformatics-unit/actions/tree/v2/build_sphinx_docs#warning).

You can run this locally to check what the behavior will be:
```
sphinx-build docs/source docs/build -b linkcheck
```
