In this tutorial, you will define admission control rules that prevent users from creating Kubernetes Ingress objects that violate the following organization policy:

* Two ingresses in different namespaces must not have the same hostname.