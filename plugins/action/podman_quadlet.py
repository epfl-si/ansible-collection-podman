import os
from uuid import uuid4

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError, AnsibleActionFail

from ansible_collections.epfl_si.actions.plugins.module_utils.ansible_api import AnsibleActions
from ansible_collections.epfl_si.actions.plugins.module_utils.subactions import Subaction

class ActionModule (ActionBase):
    @AnsibleActions.run_method
    def run (self, task_args, ansible_api):
        path = task_args.get('path')
        if path is None:
            raise AnsibleError('`path` is required')
        del task_args['path']
        content = task_args.get('content')
        if content is None:
            raise AnsibleError('`content` is required')
        del task_args['content']

        subaction = QuadletSubaction(ansible_api, self._make_tmp_path())
        errors = subaction.check_errors(path, content)
        if errors is not None:
            return dict(failed=True,
                        msg=errors)
        return subaction.copy(path, content, **task_args)


class QuadletSubaction (Subaction):
    def __init__ (self, ansible_api, tmp_path):
        super(QuadletSubaction, self).__init__(ansible_api)
        self.tmp_path = tmp_path

    def check_errors (self, path, content):
        separator = ''
        while separator in content:
            separator = uuid()

        result = self.query("shell", dict(_raw_params="""
set -e -x

checkdir="%(tmpdir)s/quadlet_check_%(uuid)s"

mkdir "$checkdir"
trap "rm -rf '$checkdir'" EXIT
cd "$checkdir"

cat > "%(basename)s" << '%(separator)s'
%(content)s
%(separator)s

env QUADLET_UNIT_DIRS="$PWD" /usr/lib/systemd/system-generators/podman-system-generator --dryrun
""" % dict(separator=separator, basename=os.path.basename(path), content=content, uuid=uuid(), tmpdir=self.tmp_path)),
                            failed_when=lambda wat: False)
        if result["rc"] == 0:
            return None
        else:
            quadlet_generator_parting_words = "".join(
                "%s\n" % l for l in result["stderr_lines"]
                if l.startswith("quadlet-generator["))
            return (quadlet_generator_parting_words if quadlet_generator_parting_words
                    else result["stderr"])

    def copy (self, path, content, **copy_args):
        return self.change(
            'copy',
            dict(
                dest=os.path.join(self.systemd_config_dir, path),
                content=content,
                **copy_args))

    @property
    def systemd_config_dir (self):
        if not hasattr(self, '__systemd_config_dir'):
            id = self.query('shell', dict(_raw_params='id -u')).rstrip()
            if id == '0':
                # No, we don't support Systemd on Windows®.
                self.__systemd_config_dir = "/etc/systemd"
            else:
                self.__systemd_config_dir = "%s/.config/containers/systemd" % self.query('shell', dict(_raw_params='echo $HOME')).rstrip()
        return self.__systemd_config_dir

def uuid ():
    return str(uuid4())
