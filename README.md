Changing the `public_access_cidrs` of the EKS Cluster produces the following preview output:

```bash
Previewing update (dev):
     Type                              Name                 Plan        Info
     pulumi:pulumi:Stack               pulumi-dev
 ~   ├─ aws-native:eks:Cluster         eks-allowlist        update      [diff: ~resourcesVpcConfig]
 +-  ├─ aws-native:iam:OidcProvider    oidc-provider        replace     [diff: ~url]
 ~   ├─ aws-native:iam:Role            vpc-cni-role         update      [diff: ~assumeRolePolicyDocument]
 +-  ├─ pulumi:providers:kubernetes    kubernetes-provider  replace     [diff: ~kubeconfig]
 +-  └─ kubernetes:helm.sh/v3:Release  nginx-ingress        replace     [diff: +compat-allowNullValues,atomic,cleanupOnFail,dependencyUpdate,description,devel,disableCRDHooks,disableOpenapiValidation,disableWebhooks,forceUpdate,keyring,lint,name,postrender,recreatePods,renderSubchartNotes,replace,resetValues,reuseValues,skipAwait,skipCr

Resources:
    ~ 2 to update
    +-3 to replace
    5 changes. 39 unchanged
```

See the [plan](pulumi-plan.json) file for more details.

Applying the change:

```bash
Updating (dev):
     Type                       Name               Status           Info
     pulumi:pulumi:Stack        pulumi-dev
 ~   └─ aws-native:eks:Cluster  eks-allowlist      updated (2s)     [diff: ~resourcesVpcConfig]

Outputs:
    cluster_name: "eks-allowlist-8884b8f"

Resources:
    ~ 1 updated
    43 unchanged

Duration: 13s
```
