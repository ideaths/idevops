# 1. Linux Guest IDs
# Amazon Linux 2 (64-bit): amazonLinux2_64Guest
# AlmaLinux (64-bit): almalinux64Guest
# Rocky Linux (64-bit): rockyLinux64Guest
# VMware Photon OS (64-bit): vmwarePhoton64Guest
# Red Hat Enterprise Linux 9 (64-bit): rhel9_64Guest
# Red Hat Enterprise Linux 8 (64-bit): rhel8_64Guest
# Red Hat Enterprise Linux 7 (64-bit): rhel7_64Guest
# Red Hat Enterprise Linux 6 (64-bit): rhel6_64Guest
# Red Hat Enterprise Linux 6 (32-bit): rhel6Guest
# CentOS 8 (64-bit): centos8_64Guest
# CentOS 7 (64-bit): centos7_64Guest
# Debian GNU/Linux 12 (64-bit): debian12_64Guest
# Debian GNU/Linux 12 (32-bit): debian12Guest
# Debian GNU/Linux 11 (64-bit): debian11_64Guest
# Debian GNU/Linux 11 (32-bit): debian11Guest
# Ubuntu Linux (64-bit): ubuntu64Guest
# Ubuntu Linux (32-bit): ubuntuGuest
# SUSE Linux Enterprise 15 (64-bit): sles15_64Guest
# FreeBSD 14 (64-bit): freebsd64Guest
# Oracle Linux 9 (64-bit): oracleLinux9_64Guest
# Other 6.x or later Linux (64-bit): other6xLinux64Guest
# Other 6.x or later Linux (32-bit): other6xLinuxGuest
# Other Linux (64-bit): otherGuest64
# Other Linux (32-bit): otherGuest
# 2. Windows Guest IDs
# Microsoft Windows Server 2025 (64-bit): windows2025_64Guest
# Microsoft Windows Server 2022 (64-bit): windows2022_64Guest
# Microsoft Windows Server 2019 (64-bit): windows9Server64Guest
# Microsoft Windows Server 2016 (64-bit): windows9Server64Guest
# Microsoft Windows Server 2012 (64-bit): windows8Server64Guest
# Microsoft Windows 11 (64-bit): windows11_64Guest
# Microsoft Windows 10 (64-bit): windows9_64Guest
# Microsoft Windows 8.x (64-bit): windows8_64Guest
# Microsoft Windows 7 (64-bit): windows7_64Guest
# Microsoft Windows XP Professional (64-bit): winXPPro64Guest
# Microsoft Windows Vista (64-bit): windowsVista_64Guest
# Microsoft Windows 2000: win2000ProGuest
# Microsoft Windows NT: winNTGuest
# Microsoft Windows 98: win98Guest
# Microsoft Windows 95: win95Guest
# Microsoft Windows 3.1: win31Guest
# 3. Other Guest IDs
# Apple macOS 12 (64-bit): darwin12_64Guest
# Apple macOS 11 (64-bit): darwin11_64Guest
# FreeBSD 13 (64-bit): freebsd13_64Guest
# IBM OS/2: os2Guest
# Novell NetWare 6.x: netware6Guest
# Oracle Solaris 11 (64-bit): solaris11_64Guest
# SCO OpenServer 6: sco6Guest
# VMware ESXi 8.0 or later: vmwareESX8Guest
# Serenity Systems eComStation 2: eComStation2Guest

locals {
  vm_groups = [
    jsondecode(file("${path.root}/list_vm/vm_templates.json"))
  ]
  vm_configs = merge(local.vm_groups...)
}

module "vcenter_vms" {
  source               = "./modules/vcenter_vm"
  for_each             = local.vm_configs
  vm_name              = each.key
  resource_pool_id     = data.vsphere_compute_cluster.cluster.resource_pool_id
  datastore_id         = data.vsphere_datastore.ds2.id
  network_id           = data.vsphere_network.network.id
  cdrom_datastore_id   = data.vsphere_datastore.ds1.id
  cdrom_path           = each.value.cdrom_path
  guest_id             = each.value.guest_id
}