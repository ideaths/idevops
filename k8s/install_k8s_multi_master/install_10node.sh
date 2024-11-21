#!/bin/bash
IP_K8Smaster01=172.16.10.52
IP_K8Smaster02=172.16.10.53
IP_K8Smaster03=172.16.10.54
IP_K8Sworker01=172.16.10.55
IP_K8Sworker02=172.16.10.56
IP_K8Sworker03=172.16.10.57
IP_K8Sworker04=172.16.10.59
IP_K8Sworker05=172.16.10.60
IP_K8Sworker06=172.16.10.61
IP_K8Sworker07=172.16.10.62
PASS_SSH_USER="Icomm@2019"
sudo apt-get update
sudo apt-get upgrade -y 
sudo apt install -y sshpass docker.io
#sudo usermod -aG docker $USER
#newgrp docker
sudo tee /etc/hosts<<EOF
127.0.0.1 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8smaster01
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.1 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
sudo systemctl restart sshd" > k8smaster01.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8smaster02
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.1 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd" > k8smaster02.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8smaster03
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.1 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd" > k8smaster03.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker01
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.0 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
" > k8sworker01.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker02
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.0 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
" > k8sworker02.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker03
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.0 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
" > k8sworker03.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker04
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.0 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
" > k8sworker04.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker05
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.0 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
" > k8sworker05.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker06
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.0 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
" > k8sworker06.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker07
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
sudo apt-get upgrade -y
sudo tee /etc/hosts<<EOF
127.0.0.0 localhost
$IP_K8Smaster01  k8smaster01
$IP_K8Smaster02  k8smaster02
$IP_K8Smaster03  k8smaster03
$IP_K8Sworker01 k8sworker01
$IP_K8Sworker02 k8sworker02
$IP_K8Sworker03 k8sworker03
$IP_K8Sworker04 k8sworker04
$IP_K8Sworker05 k8sworker05
$IP_K8Sworker06 k8sworker06
$IP_K8Sworker07 k8sworker07
EOF
sudo swapoff -a
sudo sed -i '/swap/ s/^\(.*\)$/#\1/g' /etc/fstab
sudo tee /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter
sudo tee /etc/sysctl.d/k8s.conf<<EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF
sudo sysctl --system
sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
sudo chmod 777 /etc/ssh/sshd_config
sudo echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
sudo systemctl restart sshd
" > k8sworker07.sh
sudo chmod 777 k8sworker01.sh
sudo chmod 777 k8sworker02.sh
sudo chmod 777 k8sworker03.sh
sudo chmod 777 k8smaster01.sh
sudo chmod 777 k8smaster02.sh
sudo chmod 777 k8smaster03.sh
sudo chmod 777 k8sworker04.sh
sudo chmod 777 k8sworker05.sh
sudo chmod 777 k8sworker06.sh
sudo chmod 777 k8sworker07.sh

echo "===============================install k8smaster01.sh================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster01 'bash -s' < k8smaster01.sh
echo "=============================install k8smaster02.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster02 'bash -s' < k8smaster02.sh
echo "=============================install k8smaster03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster03 'bash -s' < k8smaster03.sh
echo "=============================install k8sworker01.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker01 'bash -s' < k8sworker01.sh
echo "=============================install k8sworker02.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker02 'bash -s' < k8sworker02.sh
echo "=============================install k8sworker03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker03 'bash -s' < k8sworker03.sh
echo "======================================================================================"
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker04 'bash -s' < k8sworker04.sh
echo "=============================install k8sworker03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker05 'bash -s' < k8sworker05.sh
echo "======================================================================================"
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker06 'bash -s' < k8sworker06.sh
echo "=============================install k8sworker03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker07 'bash -s' < k8sworker07.sh
echo "======================================================================================"

echo "===============================install k8smaster01.sh================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster01 'echo "root:Icomm@2019" | sudo chpasswd'
echo "=============================install k8smaster02.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster02 'echo "root:Icomm@2019" | sudo chpasswd'
echo "=============================install k8smaster03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster03 'echo "root:Icomm@2019" | sudo chpasswd'
echo "=============================install k8sworker01.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker01 'echo "root:Icomm@2019" | sudo chpasswd'
echo "=============================install k8sworker02.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker02 'echo "root:Icomm@2019" | sudo chpasswd'
echo "=============================install k8sworker03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker03 'echo "root:Icomm@2019" | sudo chpasswd'
echo "======================================================================================"
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker04 'echo "root:Icomm@2019" | sudo chpasswd'
echo "=============================install k8sworker03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker05 'echo "root:Icomm@2019" | sudo chpasswd'
echo "======================================================================================"
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker06 'echo "root:Icomm@2019" | sudo chpasswd'
echo "=============================install k8sworker03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker07 'echo "root:Icomm@2019" | sudo chpasswd'
echo "======================================================================================"

ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8smaster01
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8smaster02
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8smaster03
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker01
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker02
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker03
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker04
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker05
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker06
sshpass -p Icomm@2019 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker07

git clone https://github.com/kubernetes-sigs/kubespray.git --branch release-2.21 /home/kubespray/

sudo tee /home/kubespray/inventory/sample/inventory.ini<<EOF
[all]
k8smaster01  ansible_host=$IP_K8Smaster01     ip=$IP_K8Smaster01
k8smaster02  ansible_host=$IP_K8Smaster02     ip=$IP_K8Smaster02
k8smaster03  ansible_host=$IP_K8Smaster03     ip=$IP_K8Smaster03
k8sworker01  ansible_host=$IP_K8Sworker01     ip=$IP_K8Sworker01
k8sworker02  ansible_host=$IP_K8Sworker02     ip=$IP_K8Sworker02
k8sworker03  ansible_host=$IP_K8Sworker03     ip=$IP_K8Sworker03
k8sworker04  ansible_host=$IP_K8Sworker04     ip=$IP_K8Sworker04
k8sworker05  ansible_host=$IP_K8Sworker05     ip=$IP_K8Sworker05
k8sworker06  ansible_host=$IP_K8Sworker06     ip=$IP_K8Sworker06
k8sworker07  ansible_host=$IP_K8Sworker07     ip=$IP_K8Sworker07

[kube_control_plane]
k8smaster01
k8smaster02
k8smaster03

[kube_node]
k8sworker01
k8sworker02
k8sworker03
k8sworker04
k8sworker05
k8sworker06
k8sworker07

[etcd]
k8smaster01
k8smaster02
k8smaster03

[k8s_cluster:children]
kube_node
kube_control_plane

[calico_rr]

[vault]
k8smaster01
k8smaster02
k8smaster03
k8sworker01
k8sworker02
k8sworker03
k8sworker04
k8sworker05
k8sworker06
k8sworker07
EOF

sudo docker run --rm -it \
  --mount type=bind,source=/home/kubespray/inventory/sample,dst=/inventory \
  --mount type=bind,source=/root/.ssh/id_rsa,dst=/root/.ssh/id_rsa \
  quay.io/kubespray/kubespray:v2.21.0 \
  bash -c "pip3 install jmespath && export ANSIBLE_HOST_KEY_CHECKING=False  && ansible-playbook -i /inventory/inventory.ini cluster.yml --user=root"
