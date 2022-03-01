# xdwarf
Mining XML to tabular data, FAAAAAAST

[![PyPI version](https://img.shields.io/pypi/v/xdwarf)](https://pypi.org/project/xdwarf)
![Python version](https://img.shields.io/pypi/pyversions/xdwarf)
![License](https://img.shields.io/github/license/raynardj/xdwarf)
![PyPI Downloads](https://img.shields.io/pypi/dm/xdwarf)

## Install
```shell
pip install xdwarf
```

The library is an wrapping on ```rust_dwarf```, a rust based mining tool.

## Mining
```python
# finding in glob pattern, project name, use all - 2 CPUs
dwarf = Dwarf.from_glob("../test/data/*.xml", "PMC",-2)
```

Define the mining detail as xpath query pattern, chaining multistage mining is well supported.
```python
dwarf.find_one('article-meta > article-id[pub-id-type=pmid]' , "pmid")
dwarf.find_one("abstract", "abstract").find_many("p", "paragraph")

# mining stage can be chained to longer detials
reference = dwarf.find_one("ref-list", "ref_list").find_many("ref","reference")
reference.find_one("pub-id[pub-id-type=pmid]", "ref_id")
reference.find_one("pub-id[pub-id-type=doi]", "doi")
ref_name = reference.find_many("name", "ref_name")
ref_name.find_one("surname", "ref_surname")
```

```python
dwarf.set_necessary("pmid")
dwarf.create_children()
```

Mining start
```python
result = dwarf()
```

See result
```python
result.child_df().head(2)
```

See child result
```python
result['ref_list'].child_df().head()
```