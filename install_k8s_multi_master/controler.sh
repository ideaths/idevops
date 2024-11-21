#!/bin/bash
IP_K8Smaster01=172.16.10.52
IP_K8Smaster02=172.16.10.53
IP_K8Smaster03=172.16.10.54
IP_K8Sworker01=172.16.10.55
IP_K8Sworker02=172.16.10.56
IP_K8Sworker03=172.16.10.57
IP_VIP=172.16.10.59
PASS_SSH_USER=1
NETWORK_INTERFACE=ens160
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
sudo apt-get install keepalived -y
sudo tee /etc/keepalived/keepalived.conf<<EOF
global_defs {
  notification_email {
  }
  router_id LVS_DEVEL
  vrrp_skip_check_adv_addr
  vrrp_garp_interval 0
  vrrp_gna_interval 0
}
vrrp_script chk_k8s {
    script  "/usr/bin/curl -s -k https://localhost:6443/healthz -o /dev/null"
    interval 20
    timeout  5
    rise     1
    fall     1
    user     root
}
vrrp_instance haproxy-vip {
  state BACKUP
  priority 100
  interface $NETWORK_INTERFACE                    
  virtual_router_id 60
  advert_int 1
  authentication {
    auth_type PASS
    auth_pass 1111
  }
  virtual_ipaddress {
    $IP_VIP/24                  
  }
  track_script {
    chk_k8s
  }
}
EOF

sudo systemctl restart keepalived
sudo systemctl enable keepalived
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
sudo apt-get install keepalived -y
sudo tee /etc/keepalived/keepalived.conf<<EOF
global_defs {
  notification_email {
  }
  router_id LVS_DEVEL
  vrrp_skip_check_adv_addr
  vrrp_garp_interval 0
  vrrp_gna_interval 0
}
vrrp_script chk_k8s {
    script  "/usr/bin/curl -s -k https://localhost:6443/healthz -o /dev/null"
    interval 20
    timeout  5
    rise     1
    fall     1
    user     root
}
vrrp_instance haproxy-vip {
  state BACKUP
  priority 100
  interface $NETWORK_INTERFACE                       # Network card
  virtual_router_id 60
  advert_int 1
  authentication {
    auth_type PASS
    auth_pass 1111
  }
  virtual_ipaddress {
    $IP_VIP/24                  # The VIP address
  }
  track_script {
    chk_k8s
  }
}
EOF

sudo systemctl restart keepalived
sudo systemctl enable keepalived
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
sudo apt-get install keepalived -y
sudo tee /etc/keepalived/keepalived.conf<<EOF
global_defs {
  notification_email {
  }
  router_id LVS_DEVEL
  vrrp_skip_check_adv_addr
  vrrp_garp_interval 0
  vrrp_gna_interval 0
}
vrrp_script chk_k8s {
    script  "/usr/bin/curl -s -k https://localhost:6443/healthz -o /dev/null"
    interval 20
    timeout  5
    rise     1
    fall     1
    user     root
}
vrrp_instance haproxy-vip {
  state BACKUP
  priority 100
  interface $NETWORK_INTERFACE                       # Network card
  virtual_router_id 60
  advert_int 1
  authentication {
    auth_type PASS
    auth_pass 1111
  }
  virtual_ipaddress {
    $IP_VIP/24                  # The VIP address
  }
  track_script {
    chk_k8s
  }
}
EOF

sudo systemctl restart keepalived
sudo systemctl enable keepalived
" > k8sworker03.sh

sudo chmod 777 k8sworker01.sh
sudo chmod 777 k8sworker02.sh
sudo chmod 777 k8sworker03.sh
sudo chmod 777 k8smaster01.sh
sudo chmod 777 k8smaster02.sh
sudo chmod 777 k8smaster03.sh

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

echo "===============================install k8smaster01.sh================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster01 'echo "root:123456" | sudo chpasswd'
echo "=============================install k8smaster02.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster02 'echo "root:123456" | sudo chpasswd'
echo "=============================install k8smaster03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8smaster03 'echo "root:123456" | sudo chpasswd'
echo "=============================install k8sworker01.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker01 'echo "root:123456" | sudo chpasswd'
echo "=============================install k8sworker02.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker02 'echo "root:123456" | sudo chpasswd'
echo "=============================install k8sworker03.sh==================================="
sshpass -p $PASS_SSH_USER ssh -o StrictHostKeyChecking=no ubuntu@k8sworker03 'echo "root:123456" | sudo chpasswd'
echo "======================================================================================"


ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1
sshpass -p 123456 ssh-copy-id -o StrictHostKeyChecking=no root@k8smaster01
sshpass -p 123456 ssh-copy-id -o StrictHostKeyChecking=no root@k8smaster02
sshpass -p 123456 ssh-copy-id -o StrictHostKeyChecking=no root@k8smaster03
sshpass -p 123456 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker01
sshpass -p 123456 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker02
sshpass -p 123456 ssh-copy-id -o StrictHostKeyChecking=no root@k8sworker03
git clone https://github.com/kubernetes-sigs/kubespray.git --branch release-2.21 /home/kubespray/

sudo tee /home/kubespray/inventory/sample/inventory.ini<<EOF
[all]
k8smaster01  ansible_host=$IP_K8Smaster01     ip=$IP_K8Smaster01
k8smaster02  ansible_host=$IP_K8Smaster02     ip=$IP_K8Smaster02
k8smaster03  ansible_host=$IP_K8Smaster03     ip=$IP_K8Smaster03
k8sworker01  ansible_host=$IP_K8Sworker01     ip=$IP_K8Sworker01
k8sworker02  ansible_host=$IP_K8Sworker02     ip=$IP_K8Sworker02
k8sworker03  ansible_host=$IP_K8Sworker03     ip=$IP_K8Sworker03

[kube_control_plane]
k8smaster01
k8smaster02
k8smaster03

[kube_node]
k8sworker01
k8sworker02
k8sworker03

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
EOF

sudo docker run --rm -it \
  --mount type=bind,source=/home/kubespray/inventory/sample,dst=/inventory \
  --mount type=bind,source=/root/.ssh/id_rsa,dst=/root/.ssh/id_rsa \
  --mount type=bind,source=/root/.ssh/id_rsa,dst=/home/ubuntu/.ssh/id_rsa  \
  quay.io/kubespray/kubespray:v2.21.0 \
  bash -c "pip3 install jmespath && export ANSIBLE_HOST_KEY_CHECKING=False  && ansible-playbook -i /inventory/inventory.ini cluster.yml --user=root"
