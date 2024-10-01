import json

import pulumi
from pulumi_aws_native import Provider
from pulumi import ResourceOptions
from pulumi_kubernetes import Provider as K8sProvider, ProviderArgs
from pulumi_aws_native.eks import (
    Cluster,
    ClusterArgs,
    ClusterResourcesVpcConfigArgs,
    Addon,
    AddonArgs,
    Nodegroup,
)
import pulumi_awsx as awsx
from pulumi_aws_native.iam import Role, RoleArgs, OidcProvider, OidcProviderArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from helper import generate_kubeconfig

awsn = Provider("awsn", region="us-east-1")

vpc = awsx.ec2.Vpc("vpc-repro-allowlist", opts=ResourceOptions(provider=awsn))

cluster_role = Role(
    resource_name="eks-role",
    args=RoleArgs(
        role_name="eks-role-allowlist",
        assume_role_policy_document=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "eks.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
        managed_policy_arns=[
            "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
            "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController",
        ],
    ),
    opts=ResourceOptions(provider=awsn),
)

cluster = Cluster(
    resource_name="eks-allowlist",
    args=ClusterArgs(
        role_arn=cluster_role.arn,
        version="1.32",
        resources_vpc_config=ClusterResourcesVpcConfigArgs(
            subnet_ids=vpc.private_subnet_ids,
            endpoint_public_access=True,
            endpoint_private_access=True,
            security_group_ids=[],
            # public_access_cidrs=["0.0.0.0/0"]
        ),
    ),
    opts=ResourceOptions(provider=awsn),
)

oidc_provider = OidcProvider(
    resource_name="oidc-provider",
    args=OidcProviderArgs(
        url=cluster.open_id_connect_issuer_url, client_id_list=["sts.amazonaws.com"]
    ),
    opts=ResourceOptions(provider=awsn),
)

vpc_cni_role = Role(
    resource_name="vpc-cni-role",
    args=RoleArgs(
        assume_role_policy_document=oidc_provider.arn.apply(
            lambda oidc_arn: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Federated": oidc_arn},
                            "Action": "sts:AssumeRoleWithWebIdentity",
                            "Condition": {
                                "StringEquals": {
                                    "/".join(oidc_arn.split("/")[1:])
                                    + ":sub": f"system:serviceaccount:kube-system:aws-node",
                                    "/".join(oidc_arn.split("/")[1:])
                                    + ":aud": "sts.amazonaws.com",
                                }
                            },
                        }
                    ],
                }
            )
        ),
        managed_policy_arns=["arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"],
    ),
    opts=ResourceOptions(provider=awsn),
)

Addon(
    resource_name="vpc-cni-addon",
    args=AddonArgs(
        cluster_name=cluster.name,
        addon_name="vpc-cni",
        service_account_role_arn=vpc_cni_role.arn,
    ),
    opts=ResourceOptions(provider=awsn),
)

node_role = Role(
    resource_name="nodes-role",
    args=RoleArgs(
        assume_role_policy_document=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
        managed_policy_arns=[
            "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
            "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
            "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
        ],
    ),
    opts=ResourceOptions(provider=awsn),
)

eks_nodegroup = Nodegroup(
    "eksNodegroup",
    cluster_name=cluster.name,
    node_role=node_role.arn,
    scaling_config={
        "min_size": 1,
        "desired_size": 1,
        "max_size": 2,
    },
    subnets=vpc.private_subnet_ids,
    opts=ResourceOptions(provider=awsn),
)

k8s = K8sProvider(
    resource_name="kubernetes-provider",
    args=ProviderArgs(
        kubeconfig=generate_kubeconfig(
            cluster_name=cluster.name,
            cluster_endpoint=cluster.endpoint,
            cert_data=cluster.certificate_authority_data,
        )
    ),
)


Release(
    "nginx-ingress",
    ReleaseArgs(
        chart="ingress-nginx",
        version="4.11.5",
        namespace="ingress",
        create_namespace=True,
        repository_opts=RepositoryOptsArgs(
            repo="https://kubernetes.github.io/ingress-nginx/",
        ),
    ),
    opts=ResourceOptions(provider=k8s),
)

pulumi.export("cluster_name", cluster.name)
