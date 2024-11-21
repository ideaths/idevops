# Triển khai cụm k8s multimaster
### Chuẩn bị Server
|Node| hostname   |      IP      |  VIP |
|:-----|----------|:-------------:|:------:|
|ControlerRemote| ControlerRemote |  10.2.65.128 |  |
|Master| k8sMaster01  | 10.2.65.150 |    |
|Master| k8sMaster02 | 10.2.65.151 |     |
|Master| k8sMaster03 | 10.2.65.152 |     |
|Worker| k8sWorker01 | 10.2.65.153 |    10.2.65.138 |
|Worker| k8sWorker02 | 10.2.65.154 |    10.2.65.138 |
|Worker| k8sWorker03 | 10.2.65.155 |    10.2.65.138 |
### Cài đặt môi trường
##### Trên Controler Remote 
Bước 1: Sửa env trên file **controler.sh**

Bước 2: Cấp quyền cho file **controler.sh**

Bước 3: Khởi chạy lần lượt **controler.sh**
```sh
sudo chmod +x controler.sh
sudo ./controler.sh
```
Quá trình cài đặt tự động khoảng 15-30p 
##### Trên tất cả các node Master
chạy các lệnh dưới đây để cấp quyền truy cập k8s
```sh 
mkdir -p $HOME/.kube
sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
# kiểm tra trạng thái các node:
kubectl get node -o wide
```
***DONE***
