import subprocess
import shutil
import os
def check_kubectl_installed():
    # Check if kubectl is installed
    return shutil.which("kubectl") is not None

def install_kubectl():
    print("Installing kubectl...")
    
    # Run the installation command for kubectl on Ubuntu
    subprocess.run(["apt-get", "update"])
    subprocess.run(["apt-get", "install", "-y", "apt-transport-https", "ca-certificates", "curl"])
    os.system("curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg")
    os.system("echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list")
    subprocess.run(["apt-get", "update"])
    subprocess.run(["apt-get", "install", "-y", "kubectl"])

    print("kubectl installed successfully.")

def main():
    if check_kubectl_installed():
        print("kubectl is already installed.")
    else:
        install_kubectl()

if __name__ == "__main__":
    main()