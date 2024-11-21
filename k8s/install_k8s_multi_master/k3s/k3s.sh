#!/bin/bash
IP_Controler=10.9.1.150
IP_K8Smaster01=10.9.1.140
IP_K8Smaster02=10.9.1.141
IP_K8Smaster03=10.9.1.142
IP_K8Sworker01=10.9.1.143
IP_K8Sworker02=10.9.1.144
IP_K8Sworker03=10.9.1.145
IP_K8Sworker04=10.9.1.146
IP_K8Sworker05=10.9.1.147
IP_K8Sworker06=10.9.1.148
IP_K8Sworker07=10.9.1.149
PASS_SSH_USER="Icomm@2019"
IP_VIP=10.9.1.151
NETWORK_INTERFACE=ens160
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo apt-get update
#sudo apt-get upgrade -y 
sudo apt install -y sshpass docker.io docker-compose

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

ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa <<<y >/dev/null 2>&1
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster01
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster02
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster03
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker01
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker02
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker03
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker04
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker05
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker06
sshpass -p $PASS_SSH_USER ssh-copy-id -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker07
sudo mkdir /opt/services
cd /opt/services
sudo mkdir -p /opt/services/mysql
sudo mkdir -p /opt/services/jenkins
sudo tee /opt/services/mysql/docker-compose.yml<<EOF
version: '3.7'
services:
  db:
    image: mysql:8.0
    command: --default-authentication-plugin=mysql_native_password
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: YNYtYMWZKc8sIzT
      MYSQL_DATABASE: kubernetes
      MYSQL_USER: kubernetes
      MYSQL_PASSWORD: YNYtYMWZKc8sIzT
    ports:
      - "3306:3306"
    volumes:
      - ./db_data:/var/lib/mysql
EOF
sudo tee /opt/services/jenkins/docker-compose.yml<<EOF
version: '3.7'
services:
  jenkins:
    image: jenkins/jenkins:2.397-jdk11
    privileged: true
    restart: always
    user: root
    ports:
      - 8080:8080
      - 50000:50000
    container_name: jenkins
    volumes:
      - ./jenkins_data:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/local/bin/docker:/usr/local/bin/docker
EOF
sudo docker-compose -f /opt/services/mysql/docker-compose.yml up -d
sudo docker-compose -f /opt/services/jenkins/docker-compose.yml up -d

#curl -s https://api.github.com/repos/goharbor/harbor/releases/latest | grep browser_download_url | cut -d '"' -f 4 | grep '\.tgz$' | wget -i -
sudo tar xvzf harbor-offline-installer*.tgz
cp harbor/harbor.yml.tmpl harbor/harbor.yml
sudo sed -i 's/hostname: reg.mydomain.com/hostname: $IP_Controler/g' /opt/services/harbor/harbor.yml
sudo sed -i 's/port: 80/port: 8000/g' /opt/services/harbor/harbor.yml
sudo sed -i 's/https:/#https:/g' /opt/services/harbor/harbor.yml
sudo sed -i 's/port: 443/#port: 443/g' /opt/services/harbor/harbor.yml
sudo sed -i 's/certificate: /#certificate: /g' /opt/services/harbor/harbor.yml
sudo sed -i 's/private_key: /#private_key: /g' /opt/services/harbor/harbor.yml
sudo sed -i 's/password: root123/password: YNYtYMWZKc8sIzT/g' /opt/services/harbor/harbor.yml
sudo /opt/services/harbor/install.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8smaster01
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
sudo apt-get install keepalived -y
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
" > k8smaster01.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8smaster02
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
sudo apt-get install keepalived -y
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
" > k8smaster02.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8smaster03
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
sudo apt-get install keepalived -y
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
" > k8smaster03.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker01
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
" > k8sworker01.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker02
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
" > k8sworker02.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker03
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
" > k8sworker03.sh

sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker04
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
" > k8sworker04.sh
sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker05
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
" > k8sworker05.sh
sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker06
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
" > k8sworker06.sh
sudo echo "#!/bin/bash
echo $PASS_SSH_USER | sudo -S sed -i /etc/sudoers -re 's/^%sudo.*/%sudo   ALL=(ALL:ALL) NOPASSWD: ALL/g'
sudo hostnamectl set-hostname k8sworker07
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
sudo apt-get update
#sudo apt-get upgrade -y
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
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster01 'bash -s' < k8smaster01.sh
echo "=============================install k8smaster02.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster02 'bash -s' < k8smaster02.sh
echo "=============================install k8smaster03.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster03 'bash -s' < k8smaster03.sh
echo "=============================install k8sworker01.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker01 'bash -s' < k8sworker01.sh
echo "=============================install k8sworker02.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker02 'bash -s' < k8sworker02.sh
echo "=============================install k8sworker03.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker03 'bash -s' < k8sworker03.sh
echo "===============================install k8sworker04.sh================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker04 'bash -s' < k8sworker04.sh
echo "=============================install k8sworker05.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker05 'bash -s' < k8sworker05.sh
echo "===============================install k8sworker06.sh================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker06 'bash -s' < k8sworker06.sh
echo "=============================install k8sworker07.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker07 'bash -s' < k8sworker07.sh
echo "======================================================================================"

curl -sLS https://get.k3sup.dev | sh
sudo install k3sup /usr/local/bin/

export DATASTORE="mysql://kubernetes:YNYtYMWZKc8sIzT@tcp($IP_Controler:3306)/kubernetes"
export TOKEN=YNYtYMWZKc8sIzT
k3sup install --user ubuntu --ip $IP_K8Smaster01 --datastore="${DATASTORE}" --token=${TOKEN} --k3s-extra-args "--disable traefik --cluster-cidr=192.168.0.0/16 --disable-network-policy --flannel-backend=none --private-registry /etc/rancher/k3s/registries.yaml"
k3sup install --user ubuntu --ip $IP_K8Smaster02 --datastore="${DATASTORE}" --token=${TOKEN} --k3s-extra-args "--disable traefik --cluster-cidr=192.168.0.0/16 --disable-network-policy --flannel-backend=none --private-registry /etc/rancher/k3s/registries.yaml"
k3sup install --user ubuntu --ip $IP_K8Smaster03 --datastore="${DATASTORE}" --token=${TOKEN} --k3s-extra-args "--disable traefik --cluster-cidr=192.168.0.0/16 --disable-network-policy --flannel-backend=none --private-registry /etc/rancher/k3s/registries.yaml"

sudo echo "#!/bin/bash
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
    script  '/usr/bin/curl -s -k https://localhost:6443/healthz -o /dev/null'
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
" > keepalived.sh
sudo chmod 777 keepalived.sh
echo "===============================install keepalived k8smaster01.sh================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster01 'bash -s' < keepalived.sh
echo "=============================install keepalived k8smaster02.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster02 'bash -s' < keepalived.sh
echo "=============================install keepalived k8smaster03.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster03 'bash -s' < keepalived.sh

ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster01 'sudo kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/tigera-operator.yaml'

ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster01 'sudo kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/custom-resources.yaml'

ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster01 'curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash'

sleep 300

k3sup join --user ubuntu --server-ip $IP_VIP --ip $IP_K8Sworker01 --k3s-extra-args "--private-registry /etc/rancher/k3s/registries.yaml"
k3sup join --user ubuntu --server-ip $IP_VIP --ip $IP_K8Sworker02 --k3s-extra-args "--private-registry /etc/rancher/k3s/registries.yaml"
k3sup join --user ubuntu --server-ip $IP_VIP --ip $IP_K8Sworker03 --k3s-extra-args "--private-registry /etc/rancher/k3s/registries.yaml"
k3sup join --user ubuntu --server-ip $IP_VIP --ip $IP_K8Sworker04 --k3s-extra-args "--private-registry /etc/rancher/k3s/registries.yaml"
k3sup join --user ubuntu --server-ip $IP_VIP --ip $IP_K8Sworker05 --k3s-extra-args "--private-registry /etc/rancher/k3s/registries.yaml"
k3sup join --user ubuntu --server-ip $IP_VIP --ip $IP_K8Sworker06 --k3s-extra-args "--private-registry /etc/rancher/k3s/registries.yaml"
k3sup join --user ubuntu --server-ip $IP_VIP --ip $IP_K8Sworker07 --k3s-extra-args "--private-registry /etc/rancher/k3s/registries.yaml"

sudo echo "#!/bin/bash
sudo mkdir /etc/rancher/k3s/
sudo tee /etc/rancher/k3s/registries.yaml<<EOF
mirrors:
  "$IP_Controler:8000":
    endpoint:
      - "http://$IP_Controler:8000"
configs:
  "$IP_Controler:8000":
    auth:
      username: admin
      password: YNYtYMWZKc8sIzT
    tls:
      insecure_skip_verify: true
EOF
sudo service k3s restart
sudo service k3s-agent restart
" > registry.sh
sudo chmod 777 registry.sh

echo "===============================install k8smaster01.sh================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster01 'bash -s' < registry.sh
echo "=============================install k8smaster02.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster02 'bash -s' < registry.sh
echo "=============================install k8smaster03.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8smaster03 'bash -s' < registry.sh
echo "=============================install k8sworker01.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker01 'bash -s' < registry.sh
echo "=============================install k8sworker02.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker02 'bash -s' < registry.sh
echo "=============================install k8sworker03.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker03 'bash -s' < registry.sh
echo "===============================install k8sworker04.sh================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker04 'bash -s' < registry.sh
echo "=============================install k8sworker05.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker05 'bash -s' < registry.sh
echo "===============================install k8sworker06.sh================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker06 'bash -s' < registry.sh
echo "=============================install k8sworker07.sh==================================="
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@k8sworker07 'bash -s' < registry.sh
echo "======================================================================================"

#kubectl config view --minify --raw
#curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
#kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/tigera-operator.yaml
#kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/custom-resources.yaml
#helm upgrade -i ingress-nginx ingress-nginx \
#--repo https://kubernetes.github.io/ingress-nginx \
#--namespace ingress-nginx --create-namespace

#https://github.com/clastix/kubelived
