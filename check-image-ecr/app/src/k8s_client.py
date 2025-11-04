import os
import time
from typing import Optional

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
import structlog


logger = structlog.get_logger()


class K8sClient:
    def __init__(self, kubeconfig: Optional[str] = None, namespace: str = "digigold"):
        self.namespace = namespace
        kubeconfig = kubeconfig or os.getenv("KUBECONFIG")
        try:
            if kubeconfig and os.path.exists(kubeconfig):
                config.load_kube_config(kubeconfig)
            else:
                config.load_incluster_config()
            self.apps_v1 = client.AppsV1Api()
        except Exception as e:
            logger.error("k8s_client_init_error", error=str(e))
            raise

    def rollout_restart(self, deployment_name: str) -> bool:
        attempts = 0
        while attempts < 3:
            attempts += 1
            try:
                body = {
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "kubectl.kubernetes.io/restartedAt": time.strftime("%Y-%m-%dT%H:%M:%S")
                                }
                            }
                        }
                    }
                }
                self.apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=self.namespace, body=body)
                logger.info("rollout_restart_triggered", deployment=deployment_name)
                return True
            except ApiException as e:
                logger.warning("rollout_restart_retry", deployment=deployment_name, attempt=attempts, status=e.status)
            except Exception as e:
                logger.warning("rollout_restart_retry_unexpected", deployment=deployment_name, attempt=attempts, error=str(e))
        logger.error("rollout_restart_failed_after_retries", deployment=deployment_name)
        return False

    def wait_until_ready(self, deployment_name: str, timeout: int = 300) -> bool:
        start = time.time()
        try:
            while time.time() - start < timeout:
                dep = self.apps_v1.read_namespaced_deployment(name=deployment_name, namespace=self.namespace)
                desired = dep.spec.replicas or 0
                ready = dep.status.ready_replicas or 0
                if desired == ready and desired > 0:
                    logger.info("deployment_ready", deployment=deployment_name, ready=ready)
                    return True
                time.sleep(5)
            logger.error("deployment_ready_timeout", deployment=deployment_name)
            return False
        except ApiException as e:
            logger.error("deployment_read_failed", deployment=deployment_name, status=e.status, reason=e.reason)
            return False
        except Exception as e:
            logger.error("deployment_read_error", deployment=deployment_name, error=str(e))
            return False