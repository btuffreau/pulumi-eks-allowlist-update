import pulumi
from pulumi import Output
import json

def generate_kubeconfig(cluster_name: pulumi.Input[str], cluster_endpoint: pulumi.Input[str],
                        cert_data: pulumi.Input[str]):
    token_command = ["eks", "get-token", "--cluster-name", cluster_name, "--output", "json"]
    env = [
        {
            "name": "KUBERNETES_EXEC_INFO",
            "value": '{"apiVersion": "client.authentication.k8s.io/v1beta1"}',
        },
    ]
    return Output.all(token_command=token_command, endpoint=cluster_endpoint, cert_data=cert_data).apply(
        lambda outputs: json.dumps({
            "apiVersion": "v1",
            "clusters": [
                {
                    "cluster": {
                        "server": outputs["endpoint"],
                        "certificate-authority-data": outputs["cert_data"],
                    },
                    "name": "kubernetes",
                },
            ],
            "contexts": [
                {
                    "context": {
                        "cluster": "kubernetes",
                        "user": "aws",
                    },
                    "name": "aws",
                },
            ],
            "current-context": "aws",
            "kind": "Config",
            "users": [
                {
                    "name": "aws",
                    "user": {
                        "exec": {
                            "apiVersion": "client.authentication.k8s.io/v1beta1",
                            "command": "aws",
                            "args": outputs["token_command"],
                            "env": env,
                        },
                    },
                },
            ],
        }))


