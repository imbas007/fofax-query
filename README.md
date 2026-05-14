# fofax-query

## API key configuration

export fofa api key
```
export FOFAAPI_KEY='fofa api key'
```

## Command line

```text
python3 fofa-query.py '<FOFA query>' [size]
```

### Examples

```bash

python3 fofa-query.py 'app="Grafana" && country="CN"' 20

python3 fofa-query.py 'body="api.telegram.org"' 20
```
