# Configuration de Proxmox pour PaaS Platform

Ce guide détaille la configuration de Proxmox VE pour une utilisation optimale avec la plateforme PaaS.

## Table des Matières

1. [Installation de Proxmox VE](#installation-de-proxmox-ve)
2. [Configuration Réseau](#configuration-réseau)
3. [Storage Configuration](#storage-configuration)
4. [Templates VM](#templates-vm)
5. [Templates LXC](#templates-lxc)
6. [Utilisateurs et Permissions](#utilisateurs-et-permissions)
7. [Optimisations](#optimisations)

## Installation de Proxmox VE

### Système requis

- CPU avec support virtualisation (Intel VT-x ou AMD-V)
- Minimum 4 GB RAM (8 GB recommandé)
- 32 GB de stockage minimum
- Connexion réseau

### Installation

1. Téléchargez l'ISO depuis [proxmox.com](https://www.proxmox.com/en/downloads)
2. Créez une clé USB bootable
3. Installez Proxmox VE
4. Accédez à l'interface web : `https://your-ip:8006`

## Configuration Réseau

### Bridge Network

Créez ou configurez un bridge pour les VMs/LXC :

```bash
# Éditer /etc/network/interfaces
auto vmbr0
iface vmbr0 inet static
    address 192.168.1.100/24
    gateway 192.168.1.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
```

### NAT (Optionnel)

Pour un réseau NAT privé :

```bash
auto vmbr1
iface vmbr1 inet static
    address 10.10.10.1/24
    bridge-ports none
    bridge-stp off
    bridge-fd 0
    post-up echo 1 > /proc/sys/net/ipv4/ip_forward
    post-up iptables -t nat -A POSTROUTING -s '10.10.10.0/24' -o vmbr0 -j MASQUERADE
    post-down iptables -t nat -D POSTROUTING -s '10.10.10.0/24' -o vmbr0 -j MASQUERADE
```

## Storage Configuration

### Types de Storage Supportés

1. **local-lvm** : Storage par défaut (LVM)
2. **local** : Stockage de fichiers (ISO, templates)
3. **NFS** : Storage réseau
4. **Ceph** : Storage distribué

### Ajouter du Storage

Via l'interface web :
1. Datacenter → Storage → Add
2. Choisissez le type de storage
3. Configurez les paramètres

## Templates VM

### Créer un Template Ubuntu 22.04

```bash
# Télécharger l'image cloud
cd /var/lib/vz/template/iso
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# Créer la VM
qm create 9000 \
  --name ubuntu-22.04-cloudinit \
  --memory 2048 \
  --cores 2 \
  --net0 virtio,bridge=vmbr0

# Importer le disque
qm importdisk 9000 jammy-server-cloudimg-amd64.img local-lvm

# Configurer le disque
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0

# Configurer cloud-init
qm set 9000 --ide2 local-lvm:cloudinit
qm set 9000 --boot c --bootdisk scsi0

# Configurer serial console
qm set 9000 --serial0 socket --vga serial0

# Activer l'agent QEMU
qm set 9000 --agent enabled=1

# Convertir en template
qm template 9000
```

### Template Debian 12

```bash
cd /var/lib/vz/template/iso
wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2

qm create 9001 \
  --name debian-12-cloudinit \
  --memory 2048 \
  --cores 2 \
  --net0 virtio,bridge=vmbr0

qm importdisk 9001 debian-12-generic-amd64.qcow2 local-lvm
qm set 9001 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9001-disk-0
qm set 9001 --ide2 local-lvm:cloudinit
qm set 9001 --boot c --bootdisk scsi0
qm set 9001 --serial0 socket --vga serial0
qm set 9001 --agent enabled=1
qm template 9001
```

## Templates LXC

### Télécharger les Templates

```bash
# Mettre à jour la liste
pveam update

# Lister les templates disponibles
pveam available

# Télécharger Ubuntu 22.04
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst

# Télécharger Debian 12
pveam download local debian-12-standard_12.2-1_amd64.tar.zst

# Télécharger Alpine (léger)
pveam download local alpine-3.18-default_20230607_amd64.tar.xz
```

### Lister les templates installés

```bash
pveam list local
```

## Utilisateurs et Permissions

### Créer un utilisateur API

```bash
# Créer l'utilisateur
pveum user add paas@pve --password <password>

# Créer un rôle personnalisé (optionnel)
pveum role add PaaS_Manager -privs "VM.Allocate VM.Clone VM.Config.CDROM VM.Config.CPU VM.Config.Cloudinit VM.Config.Disk VM.Config.HWType VM.Config.Memory VM.Config.Network VM.Config.Options VM.Monitor VM.Audit VM.PowerMgmt Datastore.AllocateSpace Datastore.Audit"

# Assigner le rôle
pveum aclmod / -user paas@pve -role PaaS_Manager
```

### Créer un token API

```bash
# Créer le token
pveum user token add paas@pve paas-token --privsep 0

# Le token sera affiché une seule fois, sauvegardez-le
```

### Utiliser le token dans l'application

Modifiez `.env` :

```env
PROXMOX_USER=paas@pve!paas-token
PROXMOX_PASSWORD=<token-secret>
```

## Optimisations

### Activer le Nested Virtualization

```bash
# Pour Intel
echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm-intel.conf

# Pour AMD
echo "options kvm_amd nested=1" > /etc/modprobe.d/kvm-amd.conf

# Reload
modprobe -r kvm_intel
modprobe kvm_intel
```

### Désactiver le Swap pour LXC

```bash
# Dans /etc/sysctl.conf
vm.swappiness = 0
```

### Configurer les Limites

Éditez `/etc/pve/datacenter.cfg` :

```
keyboard: fr
max_workers: 4
```

### Backup Automatique

1. Datacenter → Backup → Add
2. Configurez :
   - Schedule: Daily at 2:00 AM
   - Selection mode: All
   - Retention: Keep last 7

## Monitoring

### Installation de monitoring (optionnel)

```bash
apt-get install -y prometheus-node-exporter
```

### Logs

```bash
# Logs système Proxmox
journalctl -u pve*

# Logs VMs
cat /var/log/pve/tasks/active

# Logs LXC
lxc-console --name <ct-id>
```

## Sécurité

### Firewall

Activez le firewall Proxmox :

1. Datacenter → Firewall → Options
2. Activez le firewall
3. Configurez les règles

### SSL Certificate

```bash
# Installer un certificat Let's Encrypt
pvenode acme account register default mail@example.com
pvenode config set --acme domains=proxmox.example.com
pvenode acme cert order
```

### Mises à jour

```bash
# Mettre à jour Proxmox
apt-get update
apt-get dist-upgrade
```

## Ressources Utiles

- [Documentation Proxmox](https://pve.proxmox.com/pve-docs/)
- [Forum Proxmox](https://forum.proxmox.com/)
- [Wiki Proxmox](https://pve.proxmox.com/wiki/Main_Page)

## Support

Pour des questions spécifiques à cette plateforme PaaS, consultez le README principal ou ouvrez une issue sur GitHub.
