# Developers tips

If github pages fails because external links are broken, add the pages or regex at the end of the ```conf.py``` file
See [this](https://github.com/neuroinformatics-unit/actions/tree/v2/build_sphinx_docs#warning).

You can run this locally to check what the behavior will be:
```
sphinx-build docs/source docs/build -b linkcheck
```

### Running in WSL
GUI not launching in WSL.
Not optimal but found this to work:
```
export QT_QPA_PLATFORM=wayland
```

### To have WSL2 recognize bpod, follow these guidelines:
See [guidelines](./usbsinwsl.md)

Extracted from [here](https://hackmd.io/@aeefs2Y8TMms-cjTDX4cfw/r1fqAa_Da?utm_source=preview-mode&utm_medium=rec).
