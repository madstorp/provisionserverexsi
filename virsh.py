# Copyright 2014 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    'probe_virsh_and_enlist',
    ]

from lxml import etree
import pexpect
import provisioningserver.custom_hardware.utils as utils
import libvirt

test = []
user = []
SASL_USER = "root"

def request_cred(credentials, user_data):
    for credential in credentials:
        if credential[0] == libvirt.VIR_CRED_AUTHNAME:
            credential[4] = SASL_USER
        elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
		 credential[4] = "%s" % (test[0])
    return 0


def power_control_virsh(poweraddr, machine, power_change, password):
  login = poweraddr.split('@')
  user.append(login[0])
  test.append(password)
  uri = ("esx://%s?no_verify=1") % login[1]
  auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE], request_cred, None]
  conn = libvirt.openAuth(uri, auth, 0)
  data = conn.lookupByName(machine)
  if power_change == 'on':
	data.create()
  if power_change == 'off':
	data.destroy()


def probe_virsh_and_enlist(poweraddr, password=None):
    """Extracts all of the virtual machines from virsh and enlists them
    into MAAS.

    :param poweraddr: virsh connection string
    """
    conn = VirshSSH()
    if not conn.login(poweraddr, password):
        raise VirshError('Failed to login to virsh console.')

    for machine in conn.list():
        arch = conn.get_arch(machine)
        state = conn.get_state(machine)
        macs = conn.get_mac_addresses(machine)

        # Force the machine off, as MAAS will control the machine
        # and it needs to be in a known state of off.
        if state == VirshVMState.ON:
            conn.poweroff(machine)

        params = {
            'power_address': poweraddr,
            'power_id': machine,
        }
        if password is not None:
            params['power_pass'] = password
        utils.create_node(macs, arch, 'virsh', params)

    conn.logout()
