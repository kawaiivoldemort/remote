# Remote

Small utility for one command login or transferring files to machines behind jump servers/bastion hosts.

## Usage:

### Logging In

```python3
python3 remote.py login <system name>
```

### Uploading Files

```python3
python3 remote.py transfer source <system name>:destination
```

### Downloading Files

```python3
python3 remote.py transfer <system name>:source destination
```

## The `systems.json` schema

```json
"node name": {
    "user": "username",
    "host": "node host",
    "key": "node key path",
    "jump": "jump node"    
}
```

The key file and jump host are obviously optional.