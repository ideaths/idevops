# install k8s
  Master node: 

    git clone https://gitlab.com/trungduc3293/k8s.git
    cd k8s
    vim install_k8s_master.sh # change ip server
    chmod +x install_k8s_master.sh
    ./install_k8s_master.sh

  Worker node: 

    git clone https://gitlab.com/trungduc3293/k8s.git
    cd k8s
    vim install_k8s_worker.sh # change ip server
    chmod +x install_k8s_worker.sh
    ./install_k8s_worker.sh

# install helm

    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    helm create app
    helm package app
    helm install nameapp app (helm install nameapp app-...tar.gz ) 

# install nginx-ingress

    helm upgrade -i ingress-nginx ingress-nginx \
    --repo https://kubernetes.github.io/ingress-nginx \
    --namespace ingress-nginx --create-namespace \
    --set controller.metrics.enabled=true \
    --set-string controller.podAnnotations."prometheus\.io/scrape"="true" \
    --set-string controller.podAnnotations."prometheus\.io/port"="10254" --create-namespace
    
    kubectl apply --kustomize github.com/kubernetes/ingress-nginx/deploy/prometheus/

  # add cert
    kubectl -n demozone create secret tls demo-secret --cert=_.demo.vn_cachain.pem --key=_.demo.vn.pkcs8
    
# install rancher

    helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
    kubectl create namespace cattle-system
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.crds.yaml
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --version v1.11.0
    helm install rancher rancher-stable/rancher --namespace cattle-system --set hostname=rancher.demo.vn --set global.cattle.psp.enabled=false --set bootstrapPassword=admin
    kubectl -n cattle-system create secret tls rancher-cert-secret --cert=demo.pem --key=demo.pkcs8
    kubectl delete ingress rancher -n cattle-system
    vim ingress-nginx/rancher.yaml #change domain
    kubectl apply -f ingress-nginx/rancher.yaml

# install prometheus

    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm install prometheus-srv prometheus-community/prometheus -n monitor --create-namespace

# install nfs-server
    sudo apt update
    sudo apt install nfs-kernel-server -y
    sudo mkdir -p /mnt/nfs_share/
    sudo chown -R nobody:nogroup /mnt/nfs_share/
    sudo chmod 777 /mnt/nfs_share/
    sudo vi /etc/exports
    /mnt/nfs_share *(rw,sync,no_subtree_check)
    sudo exportfs -avr
    sudo systemctl restart nfs-kernel-server
    sudo ufw enable
    sudo ufw allow from 0.0.0.0/0 to any port nfs
# install nfs-client
    sudo apt install nfs-common -y
    sudo mkdir -p /mnt/nfs_clientshare
    sudo mount 10.0.2.15:/mnt/nfs_share /mnt/nfs_clientshare
