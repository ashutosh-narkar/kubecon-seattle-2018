package kubernetes.admission

import data.kubernetes.ingresses

# Policy 1: Ingress hostnames must be unique across Namespaces.
deny[msg] {
    input.request.kind.kind = "Ingress"                # Resource kind
    input.request.operation = "CREATE"                 # Resource Operation
    host = input.request.object.spec.rules[_].host     # Host making the request
    ingress = ingresses[other_ns][other_ingress]       # Iterate over ingresses
    other_ns != input.request.namespace
    ingress.spec.rules[_].host == host                 # Check if same host in the ingress rule
    msg := sprintf("invalid ingress host %q (conflicts with %v/%v)", [host, other_ns, other_ingress])
}

# Policy 2: "host" field not present in the Ingress rule.This means the Ingress rule applies for all inbound traffic.
# So the existence of an Ingress rule in any other namspace would result in a conflict.
deny[msg] {
    input.request.kind.kind = "Ingress"
    input.request.operation = "CREATE"
    x := input.request.object.spec.rules[_]
    not x.host    
    ingress = ingresses[other_ns][other_ingress]
    other_ns != input.request.namespace
    count(ingress.spec.rules) > 0
    msg := sprintf("invalid ingress host (conflicts with %v/%v)", [other_ns, other_ingress])
}
