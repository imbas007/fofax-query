# fofax-query

## API key configuration

export foofa api key
```
export FOFOAPI_KEY='fofa api key'
```

## Command line

```text
python3 fofo-query.py '<FOFA query>' [size]
```

### Examples

```bash

python3 fofo-query.py 'app="Grafana" && country="CN"' 20

python3 fofo-query.py 'body="api.telegram.org"' 20
```
