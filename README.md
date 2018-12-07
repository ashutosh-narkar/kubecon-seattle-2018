# OPA-Kube Admission Control Demo

## Prerequisites

This demo requires Kubernetes 1.9 or later. To run the tutorial locally, we recommend using minikube in version v0.28+ with Kubernetes 1.10 (which is the default).

## Setup

### Step 1: Start minikube

```bash
minikube start
```

Make sure that the minikube ingress addon is enabled:

```bash
minikube addons enable ingress
```

### Step 2: Use Minikube docker daemon on host

```bash
eval $(minikube docker-env)
```

### Step 3: Build the images for the Demo App to be deployed in the `prod` namespace

```bash
make images-prod
```

Below images should be created:

```bash
istio/examples-bookinfo-mongodb:v1
istio/examples-bookinfo-mysqldb:v1
istio/examples-bookinfo-ratings-v1:v1
istio/examples-bookinfo-ratings-v2:v1
istio/examples-bookinfo-reviews-v2:v1
istio/examples-bookinfo-details-v1:v1
istio/examples-bookinfo-productpage-v1:v1
```

### Step 4: Build the images for the Alice's version of the Demo App to be deployed in the `dev` namespace

```bash
make images-dev
```

Below images should be created:

```bash
istio/examples-bookinfo-mongodb:v2
istio/examples-bookinfo-mysqldb:v2
istio/examples-bookinfo-ratings-v1:v2
istio/examples-bookinfo-ratings-v2:v2
istio/examples-bookinfo-reviews-v2:v2
istio/examples-bookinfo-details-v1:v2
istio/examples-bookinfo-productpage-v1:v2
```

### Step 5: Create `prod` and `dev` namespaces

```bash
kubectl create ns prod
kubectl create ns dev
```

### Step 6: Deploy OPA as an Admission Controller

Follow steps 2 and 3 from the [Kubernetes Admission Controller](https://www.openpolicyagent.org/docs/kubernetes-admission-control.html) tutorial to deploy OPA as an admission controller.

## Demo

### Step 1: Deploy Demo App in `prod` namespace

```bash
kubectl apply -f demo.yaml -n prod
```

### Step 2: Open the browser and see requests routed to the Demo app

```bash
$ minikube ip
192.168.99.100
```

Use the minikube ip on the browser ie. http://192.168.99.100. You should see the landing page of the demo app showing Bob's picture and his details.

### Step 3: Deploy Alice's version of the Demo App in `dev` namespace

```bash
kubectl apply -f demo_alice.yaml -n dev
```

### Step 4: Refresh the browser

Go to http://192.168.99.100 and you should see the landing page of Alice's version of the Demo App. This time you should not see Bob's image !

> It may take 15-20 seconds for the new routes to be updated in nginx.

### Step 5: Explain why this happened

The Demo app created an ingress rule for host `*` and path `/` in the `prod` namespace. The landing page service of the demo app redirects `/` to  `/bob`.

Alice's version of the demo app created an ingress rule for host `*` and path `/bob` in the `dev` namespace.

So now when the `/` redirects to `/bob`, it matches the ingress rule created in the `dev` namespace and hence the request is handled by Alice's version of the demo app.

> Alice could have created an ingress rule for host `*` and path `/` in the `dev` namespace but the request would still be routed to the Demo app in the `prod` namespace as nginx uses the first created rule and does not overwrite it.

### Step 6: Solution - OPA as an Admission Controller

Mention that OPA has been deployed as an admission controller as part of the Demo setup.

### Step 7: Define a policy and load it into OPA

```bash
kubectl create configmap ingress-conflicts --from-file=ingress-conflicts.rego
```

This policy should reject Ingress objects in different namespaces from sharing the same hostname.

> Show the contents of the policy.

### Step 8: Redeploy Alice's version of the Demo app

```bash
kubectl delete -f demo_alice.yaml -n dev
kubectl apply -f demo_alice.yaml -n dev
```

Alice should not be able to create an Ingress in another namespace with the same hostname as the one created earlier.

### Step 9: Refresh the browser

Go to http://192.168.99.100 and this time you should see Bob's image !
