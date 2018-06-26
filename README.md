# Systeminfo

Systeminfo is a python package that was created to maintain a systems information.
Whether it be what packages are installed, what is the system temp is, or
something else, this would be able to give you a programmable interface to that
information.

## Installation
To install, use pip or pipenv

```bash
pip install -e .
pipenv install -e .
```
Or install from the git repository
```bash
TODO get url
```

## Usage
Simply import `systeminfo` and create an instance of whatever system you are
working on. Currently the `System` class is the one you should use.
```python
import systeminfo

localhost = systeminfo.System()
```

System supports querying the system for what packages are installed via `apt`
and `pip`. To get all the packages installed by both, use the `.get_dict()` or
`.async_get_dict()` methods. If you simply want to search the packages, use
`.search()` or `.async_search()`

By default the search does a fuzzy match, if the package name and version
contains the search terms, it is considered a match. For example:
```python
localhost.search('vim', version='2')

[{'from': 'apt', 'name': 'vim', 'version': '2:8.0.1453-1ubuntu1', 'arch': 'amd64', 'state': '[installed]'}, {'from': 'apt', 'name': 'vim-tiny', 'version': '2:8.0.1453-1ubuntu1', 'arch': 'amd64', 'state': '[installed]'}, {'from': 'apt', 'name': 'vim-common', 'version': '2:8.0.1453-1ubuntu1', 'arch': 'all', 'state': '[installed]'}, {'from': 'apt', 'name': 'vim-runtime', 'version': '2:8.0.1453-1ubuntu1', 'arch': 'all', 'state': '[installed]'}]
```
All the packages contain the word `vim` and all the versions contains `2`. If
you would like to get exact matches on the name, set `match=True`. Note that
this does not match exact for the version, just the name.
```python
localhost.search('python3', match=True)

[{'from': 'apt', 'name': 'python3', 'version': '3.6.5-3', 'arch': 'amd64', 'state': '[installed]'}]
```


### Specific Information classes
There exist some special classes for specific needs.

* `Singularity`: Used for executing things inside a Singularity container


## Web
This repo contains a small web server that acts as a front end to systeminfo.
To run, install the dependencies and call `app.py` from within the `web` folder.

```bash
cd web
pipenv install
python3 app.py
```

### Quick API overview
The site can be used with query strings or headers, whichever you prefer. The
examples will show the query string method, but read the docstrings to see what
headers you need.

There are two keys, `query` and `format`.

* `query`: is the query to perform; A comma separated list of query terms
    * `query=vim`
    * `query=emacs,python=3`
* `format`: What format do you want the data in? Currently supports `xml`, `json`, and `html`

You must perpend a `?` to the start and separate the keys with a `&`. Order does not matter.
* `?format=xml&query=tensorflow`


## Development
Check the issues, feel free to make a merge request
