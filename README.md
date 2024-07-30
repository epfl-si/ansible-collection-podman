# Ansible Collection - epfl_si.podman

## `epfl_si.podman.podman_quadlet` module

Example usage:

```yaml
- name: Sample MariaDB database
  epfl_si.podman.podman_quadlet:
    path: mariadb.container
    content: |
      [Unit]
      Description=Podman container mariadb.service

      [Container]
      Image=docker.io/library/mariadb:11

      [Install]
      WantedBy=default.target
```

- Takes the same options as the `copy` module to specify e.g. file modes
- If a relative path is used for `path`, the quadlet will be installed within the correct directory i.e. `/etc/systemd/system` if running as root, or `$HOME/.config/containers/systemd` otherwise.
