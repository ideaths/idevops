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

