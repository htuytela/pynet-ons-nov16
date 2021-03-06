#!/usr/bin/python
"""
(c) 2016 Elisa Jasinska <elisa@bigwaveit.org>
    Original prototype by David Barroso <dbarrosop@dravetech.com>
"""

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

RETURN = '''
'''

try:
    from napalm_base import get_network_driver
except ImportError:
    napalm_found = False
else:
    napalm_found = True

def save_to_file(content, filename):
    f = open(filename, 'w')
    try:
        f.write(content)
    finally:
        f.close()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(type='str', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            timeout=dict(type='int', required=False, default=60),
            optional_args=dict(required=False, type='dict', default=None),
            config_file=dict(type='str', required=True),
            dev_os=dict(type='str', required=True,
                choices=['eos', 'junos', 'iosxr', 'fortios', 'ibm', 'ios', 'nxos', 'panos']),
            commit_changes=dict(type='bool', required=True),
            replace_config=dict(type='bool', required=False, default=False),
            diff_file=dict(type='str', required=False, default=None),
            get_diffs=dict(type='bool', required=False, default=True)
        ),
        supports_check_mode=True
    )

    if not napalm_found:
        module.fail_json(msg="the python module napalm is required")

    hostname = module.params['hostname']
    username = module.params['username']
    dev_os = module.params['dev_os']
    password = module.params['password']
    timeout = module.params['timeout']
    config_file = module.params['config_file']
    commit_changes = module.params['commit_changes']
    replace_config = module.params['replace_config']
    diff_file = module.params['diff_file']
    get_diffs = module.params['get_diffs']

    if module.params['optional_args'] is None:
        optional_args = {}
    else:
        optional_args = module.params['optional_args']

    try:
        network_driver = get_network_driver(dev_os)
        device = network_driver(hostname=hostname,
                                username=username,
                                password=password,
                                timeout=timeout,
                                optional_args=optional_args)
        device.open()
    except Exception, e:
        module.fail_json(msg="cannot connect to device: " + str(e))

    try:
        if replace_config:
            device.load_replace_candidate(filename=config_file)
        else:
            device.load_merge_candidate(filename=config_file)
    except Exception, e:
        module.fail_json(msg="cannot load config: " + str(e))

    try:
        if get_diffs:
            diff = device.compare_config().encode('utf-8')
            changed = len(diff) > 0
        else:
            changed = True
            diff = None
        if diff_file is not None and get_diffs:
            save_to_file(diff, diff_file)
    except Exception, e:
        module.fail_json(msg="cannot diff config: " + str(e))

    try:
        if module.check_mode or not commit_changes:
            device.discard_config()
        else:
            if changed:
                device.commit_config()
    except Exception, e:
        module.fail_json(msg="cannot install config: " + str(e))

    try:
        device.close()
    except Exception, e:
        module.fail_json(msg="cannot close device connection: " + str(e))

    module.exit_json(changed=changed, msg=diff)

# standard ansible module imports
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
